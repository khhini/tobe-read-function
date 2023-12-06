# To Be Read Function

A simple functions that will generated article metadata from given article url and save them to Notion as pages.

## Create Service Account
```
gcloud iam service-accounts create tobe-read-sa \
  --project=(gcloud config get-value project)

```
## Create Pub/Sub Topics
```
gcloud pubsub topics create tobe-read-topic
```
## Deploy Cloud Function
```
gcloud functions deploy tobe-read-function \
      --region=asia-southeast2 \
      --runtime=python310 \
      --source=https://source.developers.google.com/projects/$PROJECT_ID/repos/$REPOSITORY_NAME \
      --entry-point=cloudevent_function \
      --service-account=tobe-read-sa@khhini-porto-web-prod.iam.gserviceaccount.com \
      --set-env-vars=NOTION_API_KEY=$NOTION_API_KEY \
      --set-env-vars=NOTION_DATABASE_ID=$NOTION_DATABSE_ID \
      --trigger-topic=tobe-read-topic
```