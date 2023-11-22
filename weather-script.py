from time import sleep

import requests
from elasticsearch import Elasticsearch
from datetime import datetime, timezone
import os
from kubernetes import client, config
import base64
from requests.auth import HTTPBasicAuth


def fetch_weather(api_key, city):
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data for {city}: {e}")
        return None


def push_to_elasticsearch(es, index, document):
    try:
        es.index(index=index, body=document)
        print(f"Data pushed to Elasticsearch: {document}")
    except Exception as e:
        print(f"Error pushing data to Elasticsearch: {e}")


def get_api_key_from_secret():
    try:
        config.load_incluster_config()  # Load in-cluster config for running inside a pod
        v1 = client.CoreV1Api()
        secret_name = "weather-secret"

        # Retrieve the secret data
        secret = v1.read_namespaced_secret(secret_name, "default")
        api_key_base64 = secret.data.get("api_key", None)

        if api_key_base64:
            api_key_bytes = base64.b64decode(api_key_base64)
            api_key = api_key_bytes.decode("utf-8").strip()

            return api_key

    except Exception as e:
        print(f"Error retrieving API key from Kubernetes secret: {e}")

    return None


def get_elasticsearch_credentials():
    try:
        config.load_incluster_config()  # Load in-cluster config for running inside a pod
        v1 = client.CoreV1Api()
        secret_name = "elasticsearch-master-credentials"

        # Retrieve the secret data
        secret = v1.read_namespaced_secret(secret_name, "default")
        es_username_base64 = secret.data.get("username", None)
        es_password_base64 = secret.data.get("password", None)

        if es_username_base64 and es_password_base64:
            es_username = base64.b64decode(es_username_base64).decode("utf-8").strip()
            es_password = base64.b64decode(es_password_base64).decode("utf-8").strip()

            return es_username, es_password

    except Exception as e:
        print(f"Error retrieving Elasticsearch credentials from Kubernetes secret: {e}")

    return None, None


def main():
    api_key = get_api_key_from_secret()
    if not api_key:
        print("API key not found in Kubernetes secret.")
        return

    es_username, es_password = get_elasticsearch_credentials()

    # Check if credentials are available
    if es_username and es_password:
        es = Elasticsearch(
            [{"host": "elasticsearch-master.default.svc.cluster.local", "port": 9200, "scheme": "http"}],
            basic_auth=(es_username, es_password),
        )
        index = "weather-data"
    else:
        es = ""
        index = "weather-data"
    cities = ["Jerusalem", "New York", "London", "Paris", "Tokyo"]

    node_name = os.environ.get('NODE_NAME')
    pod_name = os.environ.get('POD_NAME')

    metadata = {"pod_name": pod_name, "node_name": node_name}

    # node_name = get_node_name()
    # print(f"Node Name: {node_name}")

    # pod_and_node_metadata = get_pod_and_node_name()
    # metadata.update(pod_and_node_metadata)

    for city in cities:
        # weather_data, metadata = fetch_weather(api_key, city, metadata)
        weather_data = fetch_weather(api_key, city)
        if weather_data:
            timestamp = datetime.now(timezone.utc).isoformat()
            document = {
                "timestamp": timestamp,
                "city": city,
                "temperature": weather_data["current"]["temp_c"],
                "humidity": weather_data["current"]["humidity"],
                "weather_description": weather_data["current"]["condition"]["text"],
                "metadata": metadata,
            }
            print(f"document: {document}")
            push_to_elasticsearch(es, index, document)
        sleep(30)


if __name__ == "__main__":
    main()
