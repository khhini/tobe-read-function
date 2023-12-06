import os
import requests
import structlog
import functions_framework
import base64
import json

from newspaper import Article
from dotenv import load_dotenv

try:
  load_dotenv()
except Exception:
  pass

#Setup Logger
structlog.configure(
  processors=[
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
    structlog.processors.JSONRenderer(),
  ],
  context_class=dict,
  logger_factory=structlog.PrintLoggerFactory(),
  wrapper_class=structlog.stdlib.BoundLogger,
  cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")

# @functions_framework.cloud_event
def cloudevent_function(event_data, context):
  data = json.loads(base64.b64decode(event_data["data"]).decode())
  
  article_data = extract_article_data(data["article_url"])
  request_body = generate_request_body(article_data)
  post_notion_page(request_body)


def extract_article_data(url):
  article = Article(url)
  article.download()
  article.parse()
  
  return {
    "url": article.url,
    "title": article.title,
    "authors": article.authors,
    "publish_date": article.publish_date.strftime("%Y-%m-%d") if article.publish_date else None,
    "tags": list(article.tags),
    "description": article.meta_description,
  }

def generate_request_body(article_data): 
  request_body = {
     "parent": {
        "type": "database_id",
        "database_id": "{}".format(NOTION_DATABASE_ID)
    },
    "properties": {}
  }
  
  title = {
    "type": "title",
    "title": [{
      "type": "text",
      "text": {"content": "{}".format(article_data["title"])}
    }]
  }
  
  link = {
    "type": "url",
    "url": article_data["url"]
  }
  
  authors = {
    "type": "multi_select",
    "multi_select": [{"name": x} for x in article_data["authors"]]
  }
  
  publish_date = {
    "type": "date",
    "date": {
      "start": article_data["publish_date"]
    } if article_data["publish_date"] else None
  } 
  
  description = {
    "type": "rich_text",
    "rich_text": [{
      "type": "text",
      "text": {
        "content": article_data["description"]
      }
    }]
  }
  
  tags = {
    "type": "multi_select",
    "multi_select": [{"name": x} for x in article_data["tags"]]
  }
  
  
  request_body["properties"]["Title"] = title
  request_body["properties"]["Link"] = link
  request_body["properties"]["Authors"] = authors
  request_body["properties"]["Publish Date"] = publish_date
  request_body["properties"]["Description"] = description
  request_body["properties"]["Tags"] = tags
  
  return request_body

def post_notion_page(request_body):
  url = 'https://api.notion.com/v1/pages'
  
  headers = {
    "Authorization": "Bearer {}".format(NOTION_API_KEY),
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
  }
  
  response = requests.post(url, json=request_body, headers=headers)
  
  if response.status_code == 200:
    logger.info("Success adding page to database", input=request_body["properties"]["Link"]['url'], result=response.json(), status="succes")
  else:
    logger.error("Success adding page to database", input=request_body["properties"]["Link"]['url'], result=response.json(), error=response.text)

    