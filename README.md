# k8s-weather-app

This is a helm chart that deploys elastic search with custom values and creates all the needed secrets and roles to run the Python script to retrieve data from weather API and push it to elastic search.

## Commands to run:

First, git clone the repo into your computer, then once the files are downloaded run the following command in k8s-weather-app/weather-app-chart:
```
helm dependency update ./weather-app 
helm package ./weather-app
helm install weather-app ./weather-app-0.2.0.tgz -f weather-app/values.yaml
```
