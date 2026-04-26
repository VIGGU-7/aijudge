import json
import logging
from google.cloud import pubsub_v1
from app.core.config import settings
from app.schemas.events import SubmissionCreatedEvent

logger = logging.getLogger(__name__)

class IPublisherService:
    """
    Interface for Pub/Sub operations.
    """
    async def publish_submission_created(self, event: SubmissionCreatedEvent) -> str: ...

class GcpPublisherService:
    """
    Google Cloud Pub/Sub implementation.
    """
    def __init__(self):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(settings.PROJECT_ID, settings.SUBMISSION_TOPIC)

    async def publish_submission_created(self, event: SubmissionCreatedEvent) -> str:
        """
        Publishes the submission created event to the configured topic.
        """
        try:
            # Pydantic handles the serialization to dict
            data = event.model_dump_json().encode("utf-8")
            
            # Attributes can be used for subscription filtering
            attributes = {
                "version": event.version,
                "submission_id": event.submission_id,
                "hackathon_id": event.hackathon_id
            }
            
            future = self.publisher.publish(self.topic_path, data, **attributes)
            message_id = future.result()
            
            logger.info(f"Published event {event.submission_id} with Message ID: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to publish event to Pub/Sub: {str(e)}")
            # In production, we might want to throw or use an outbox pattern
            raise

def get_publisher_service() -> GcpPublisherService:
    return GcpPublisherService()
