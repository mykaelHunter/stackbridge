# StackBridge

internal platform for orders and users

## running it

```
docker-compose up
```

app is on port 5000

db is postgres on 5432

## infra

terraform is in infra/legacy. you need AWS creds.
ask jake for the state file if you don't have it.
do not run terraform destroy.

## database

schema is in database/schema.sql
to reset the db: docker-compose down -v then up again
for prod: ask jake

## deploying

SSH into the server and pull the latest docker image.
Server IP: ask jake (it changes sometimes)

## on call

if something breaks, message the #dev channel
jake usually responds

## known issues

- the /internal/debug endpoint should be removed but we need it for now
- staging and prod use the same db password (for now)
- backups: jake does these manually, see him for the schedule
- the orders endpoint is a bit slow sometimes, not sure why
- don't touch the terraform state file

## contacts

jake (left the company in march)
Now that you have been hired as the first platform engineer at StackBridge. This repository is everything Jake left behind. Your job starts here.
