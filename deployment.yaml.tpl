apiVersion: apps/v1
kind: Deployment

metadata:
  name: {{SERVICE_NAME}}

spec:
  replicas: 2

  selector:
    matchLabels:
      app: {{SERVICE_NAME}}

  template:
    metadata:
      labels:
        app: {{SERVICE_NAME}}

    spec:
      containers:
      - name: {{SERVICE_NAME}}
        image: {{IMAGE_REPOSITORY}}:{{IMAGE_TAG}}
        imagePullPolicy: IfNotPresent

        ports:
        - containerPort: {{PORT}}
