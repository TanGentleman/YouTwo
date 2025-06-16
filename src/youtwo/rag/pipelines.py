import os
import logging
from youtwo.rag.backend import get_source_filenames_from_convex, process_document_batch, upload_sources_to_convex
from youtwo.rag.vectara_client import VectaraClient

logger = logging.getLogger(__name__)


def sync_vectara_to_convex(max_docs: int = 20, batch_size: int = 10) -> bool:
    """Process documents from Vectara and send to Convex in batches"""
    try:
        # Get existing chunks from Convex
        existing_filenames = get_source_filenames_from_convex()

        # Fetch document IDs from Vectara
        client = VectaraClient()
        docs = client.get_corpus_info(limit=50)
        logger.debug(f"Retrieved {len(docs)} documents from Vectara")

        # Filter out existing documents
        id_list = [doc["id"] for doc in docs if doc["id"] not in existing_filenames]

        if not id_list:
            logger.info("No new documents to process")
            return True

        logger.info(
            f"Processing {min(max_docs, len(id_list))} of {len(id_list)} new documents"
        )

        # Setup document storage
        folder_path = os.path.join(os.path.dirname(__file__), "vectara_documents")

        all_success = True

        # Process documents in batches
        for batch_start in range(0, min(max_docs, len(id_list)), batch_size):
            batch_ids = id_list[batch_start : batch_start + batch_size]
            processed_sources = process_document_batch(batch_ids, folder_path)

            # Send batch if we have any chunks
            if not processed_sources:
                logger.warning(
                    f"No valid sources in batch {batch_start}-{batch_start + batch_size}"
                )
                continue

            result = upload_sources_to_convex(
                processed_sources,
            )

            if not result["ok"]:
                logger.error(
                    f"Failed to send batch {batch_start}-{batch_start + batch_size}"
                )
                all_success = False
            else:
                logger.info(f"Sent batch with {len(processed_sources)} sources")

        return all_success

    except Exception as e:
        logger.error(f"Sync failed: {str(e)}", exc_info=True)
        return False