#!/bin/bash
# deploy.sh
# HOW WE DEPLOY TO PROD
# run this from your laptop when you want to deploy
# make sure you have the PEM file

SERVER_IP="54.123.456.78"   # update this if it changes (it changes)
PEM_FILE="~/.ssh/stackbridge-prod.pem"

echo "deploying to prod..."

# copy files to server
scp -i $PEM_FILE -r ./app ubuntu@$SERVER_IP:/home/ubuntu/app

# SSH in and restart
ssh -i $PEM_FILE ubuntu@$SERVER_IP << 'EOF'
  cd /home/ubuntu/app
  pip3 install -r requirements.txt --quiet
  pkill -f "python3 app.py" || true
  nohup python3 app.py > app.log 2>&1 &
  echo "deployed"
EOF

echo "done. check http://$SERVER_IP:5000/health"
echo "if it is broken, SSH in and check app.log"
# to rollback: SSH in and run the previous version manually
