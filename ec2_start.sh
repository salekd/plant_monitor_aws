#!/bin/bash
sudo service postgresql start

cd /home/ec2-user/plant_monitor_aws && sudo nohup python flask_app.py > /home/ec2-user/flask_app.out 2>&1 &

sudo service docker start
sudo nohup docker run -p 80:8080 -e SWAGGER_JSON=/spec/swagger.json -e VALIDATOR_URL=null -v /home/ec2-user/plant_monitor_aws/:/spec swaggerapi/swagger-ui > /home/ec2-user/swagger-ui.out 2>&1 &

sudo nohup jupyterhub > /home/ec2-user/jupyterhub.out 2>&1 &
