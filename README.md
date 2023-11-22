# k8s-weather-app

This is a helm chart that is deploying elastic search with custom values, and also creating all the needed secrets and roles in order to run the python script in order to retrieve data from weatherapi and push it to elastic search.

## Commands to run:

First git clone the repo into your computer, then once the files are downloaded run in the follwoing commnad in k8s-weather-app/weather-app-chart:
```
helm dependency update ./weather-app 
helm package ./weather-app
helm install weather-app ./weather-app-0.2.0.tgz -f weather-app/values.yaml
```
