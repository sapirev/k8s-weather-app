import requests
from elasticsearch import Elasticsearch
from datetime import datetime, timezone
import os
from kubernetes import client, config
import base64


def fetch_weather(api_key, city, metadata):
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()
        return data, metadata
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data for {city}: {e}")
        return None, metadata


def get_node_name():
    try:
        response = requests.get("https://kubernetes.default.svc.cluster.local:50900/api/v1/nodes", headers={
            "Authorization": f"Bearer {open('/run/secrets/kubernetes.io/serviceaccount/token').read().strip()}"})

        response.raise_for_status()
        node_name = response.json()["items"][0]["metadata"]["name"]
        return node_name
    except Exception as e:
        print(f"Error retrieving node name: {e}")
        return None


def get_pod_and_node_name():
    try:
        with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace", "r") as file:
            namespace = file.read().strip()

        with open("/var/run/secrets/kubernetes.io/serviceaccount/podname", "r") as file:
            pod_name = file.read().strip()

        with open("/var/run/secrets/kubernetes.io/serviceaccount/nodename", "r") as file:
            node_name = file.read().strip()

        return {"pod_name": pod_name, "namespace": namespace, "node_name": node_name}
    except Exception as e:
        print(f"Error retrieving pod and node name: {e}")
        return {}


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

        print(f"Base64-encoded API key: {api_key_base64}")

        if api_key_base64:
            api_key_bytes = base64.b64decode(api_key_base64)
            api_key = api_key_bytes.decode("utf-8").strip()

            print(f"API key: {api_key}")
            return api_key

    except Exception as e:
        print(f"Error retrieving API key from Kubernetes secret: {e}")

    return None


def main():
    api_key = get_api_key_from_secret()
    if not api_key:
        print("API key not found in Kubernetes secret.")
        return

    es = Elasticsearch([{"host": "elasticsearch-master.default.svc.cluster.local", "port": 9200, "scheme": "http"}])
    index = "weather-data"

    cities = ["Jerusalem", "New York", "London", "Paris", "Tokyo"]
    metadata = {"additional_info": "your_metadata_here"}

    node_name = get_node_name()
    print(f"Node Name: {node_name}")

    pod_and_node_metadata = get_pod_and_node_name()
    metadata.update(pod_and_node_metadata)

    for city in cities:
        weather_data, metadata = fetch_weather(api_key, city, metadata)
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
            push_to_elasticsearch(es, index, document)


if __name__ == "__main__":
    main()
