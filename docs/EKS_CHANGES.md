# EKS Addition + Corrections — Summary

## Why EKS was missing in the first place

Teammates added Argo Rollouts manifests, an ArgoCD Application pointing at
those manifests, and a payment-api service with its own k8s/ directory — all
of which assume a running Kubernetes cluster. There was no cluster anywhere
in `infra/`. This was the actual gap: the GitOps/canary layer had nothing
underneath it to deploy onto.

---

## What was fixed

### 1. Deprecated `dynamodb_table` backend parameter
**Files:** `infra/environments/dev/main.tf`, `infra/environments/staging/main.tf`

Terraform now warns that `dynamodb_table` in the S3 backend block is
deprecated in favor of `use_lockfile`, which uses native S3 conditional
writes for state locking instead of a separate DynamoDB table.

```hcl
# Before
backend "s3" {
  bucket         = "stackbridge-tf-state"
  key            = "environments/dev/terraform.tfstate"
  region         = "us-east-1"
  dynamodb_table = "stackbridge-tf-lock"
  encrypt        = true
}

# After
backend "s3" {
  bucket       = "stackbridge-tf-state"
  key          = "environments/dev/terraform.tfstate"
  region       = "us-east-1"
  use_lockfile = true
  encrypt      = true
}
```

**Requires Terraform >= 1.10.** If your CI runner pins an older version,
bump `hashicorp/setup-terraform` in the workflow.

The old `stackbridge-tf-lock` DynamoDB table is now unused — safe to delete
once you've confirmed both environments apply cleanly with the new backend.

### 2. EKS subnet discovery tags
**File:** `infra/modules/network/main.tf`

Public and private subnets now carry the tags EKS needs to function:

- Public subnets: `kubernetes.io/role/elb = 1` — lets the AWS Load Balancer
  Controller place internet-facing ELBs/ALBs here automatically.
- Private subnets: `kubernetes.io/role/internal-elb = 1` — same, for
  internal load balancers.
- Both: `kubernetes.io/cluster/<name>-<environment> = shared` — cluster
  autodiscovery tag.

Without these, the Load Balancer Controller (which you'll likely install
next, given the Argo Rollouts setup) can't find anywhere to place a
LoadBalancer-type Service.

**This is a destructive-looking but actually safe change** — Terraform will
show a tag update on existing subnets, not a replace. No downtime.

---

## What was added

### `infra/modules/eks/` — new module

A complete EKS module: cluster, IAM roles (cluster + node), OIDC provider
for IRSA, a managed node group, and an EKS access entry so whoever runs
`terraform apply` gets `kubectl` access automatically via the modern
access entry API (not the legacy `aws-auth` ConfigMap).

**Free tier honesty, upfront:** the EKS control plane is not free-tier
eligible — it's a flat ~$0.10/hour (~$73/month) regardless of cluster size,
node count, or usage. There is no Terraform setting that changes this; it's
an AWS pricing decision. What *is* free-tier-eligible is the worker node
EC2 usage (750 hrs/month of t2.micro/t3.micro), which is why the module
defaults to nodes, not the control plane, as the cost lever.

`t3.small` was chosen over `t3.micro` for nodes because `t3.micro`'s 1GB RAM
is mostly consumed by kubelet, kube-proxy, and the VPC CNI plugin before any
of your actual pods get scheduled — it technically joins the cluster but is
not practically usable. `t3.small` (2GB) is the realistic floor.

| Environment | Nodes | Why |
|---|---|---|
| dev | 1 | Minimum viable — just enough to deploy and test |
| staging | 2 | Argo Rollouts canary steps need at least 2 schedulable nodes to demonstrate a real rolling update, not just a restart |

Both environments wired into `main.tf` and produce three new outputs:
`eks_cluster_name`, `eks_cluster_endpoint`, `eks_kubeconfig_command`.

---

## What you need to do manually

### Remove already-committed plan artifacts from git history
`.gitignore` already has rules for `tfplan.binary` / `tfplan.json`, but
those rules only block *future* commits — the files currently in the repo
were committed before the rules existed. Run:

```bash
git rm --cached infra/environments/dev/tfplan.binary
git rm --cached infra/environments/dev/tfplan.json
git rm --cached infra/tfplan.json
git commit -m "chore: stop tracking generated plan artifacts"
```

### After applying, connect kubectl
```bash
terraform output eks_kubeconfig_command
# copy/run the output, e.g.:
aws eks update-kubeconfig --name stackbridge-dev --region us-east-1

kubectl get nodes   # should show 1 (dev) or 2 (staging) Ready nodes
```

### Get ArgoCD and Argo Rollouts actually installed
The manifests your teammates wrote (`kubernetes/argocd/argocd-app.yaml`,
`kubernetes/argo-rollouts/*.yaml`) assume the Argo Rollouts and ArgoCD
*controllers* are already running in the cluster — Terraform doesn't
install these (that's an app-layer concern, not infra). After `kubectl`
is connected:

```bash
# ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Argo Rollouts
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

Then the existing `argocd-app.yaml` and `stackbridge-flask.yaml` manifests
should apply cleanly.

### OPA policy gap
The existing `infra/policies/security.rego` doesn't yet have rules for EKS
(e.g. blocking public API endpoint access in prod, enforcing node group
tagging). Worth a follow-up — happy to add EKS-specific Conftest rules if
you want the same policy-as-code enforcement applied to the new module.

---

## Cost summary (us-east-1, approximate)

| Resource | Free tier? | Approx cost if not |
|---|---|---|
| EKS control plane (dev) | No | ~$73/mo |
| EKS control plane (staging) | No | ~$73/mo |
| 1× t3.small node (dev) | Partial — EC2 hours only | ~$15/mo |
| 2× t3.small nodes (staging) | Partial | ~$30/mo |

**Running both dev and staging EKS clusters continuously costs roughly
$190/month even at minimum sizing** — this is the one place in the whole
project where "free tier" and "EKS" are fundamentally in tension. Worth
discussing with your team whether to run EKS only in one shared environment,
or spin clusters up/down on demand via the CLI rather than leaving them
running 24/7.
