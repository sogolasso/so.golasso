import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='data/scraper.log',
                    filemode='a')
logger = logging.getLogger('firebase_handler')

# Initialize Firebase
firebase_app = None

# So Golasso Firebase Config
FIREBASE_PROJECT_ID = "so-golasso"
FIREBASE_CONFIG = {
    "projectId": FIREBASE_PROJECT_ID,
    "apiKey": "AIzaSyD0zYSxZQH5Qx2XDBfRmWV9rxVw5y2LMdw",
    "authDomain": "so-golasso.firebaseapp.com",
    "storageBucket": "so-golasso.firebasestorage.app",
    "messagingSenderId": "284164830547",
    "appId": "1:284164830547:web:0b31e64f4c16d13c6f1da6",
    "measurementId": "G-51YSSB3PQ3"
}

def initialize_firebase():
    """
    Initializes Firebase with service account credentials or default config
    """
    global firebase_app
    
    try:
        # Check if Firebase is already initialized
        if firebase_app:
            return firebase_app
            
        # Try to load service account credentials
        cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
        
        if os.path.exists(cred_path):
            # Initialize with service account credentials
            cred = credentials.Certificate(cred_path)
            firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with service account credentials")
        else:
            # Initialize with default config
            logger.warning("Firebase service account credentials not found, initializing with default config")
            try:
                firebase_app = firebase_admin.initialize_app(options={
                    'projectId': FIREBASE_PROJECT_ID,
                    'storageBucket': FIREBASE_CONFIG['storageBucket']
                })
                logger.info("Firebase initialized with default config")
            except ValueError as e:
                if 'The default Firebase app already exists' in str(e):
                    firebase_app = firebase_admin.get_app()
                    logger.info("Retrieved existing Firebase app")
                else:
                    raise e
        
        return firebase_app
        
    except Exception as e:
        logger.error(f"Error initializing Firebase: {str(e)}")
        return None

def get_firestore_db():
    """
    Gets the Firestore database instance with retries
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            if not firebase_app:
                initialize_firebase()
            
            if firebase_app:
                return firestore.client()
            else:
                logger.error("Firebase not initialized")
                return None
                
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Error getting Firestore client (attempt {retry_count}/{max_retries}): {str(e)}")
                time.sleep(2 ** retry_count)  # Exponential backoff
            else:
                logger.error(f"Failed to get Firestore client after {max_retries} attempts: {str(e)}")
                return None

def save_to_firebase(collection_name, data_list):
    """
    Saves data to Firebase Firestore with retries and batch processing
    
    Args:
        collection_name (str): The name of the collection to save to
        data_list (list): The list of data items to save
    """
    if not data_list:
        logger.warning("No data to save to Firebase")
        return
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Initialize Firebase if not already initialized
            if not firebase_app:
                initialize_firebase()
            
            if not firebase_app:
                logger.error("Firebase not initialized, cannot save data")
                return
            
            # Get Firestore database
            db = get_firestore_db()
            
            if not db:
                logger.error("Could not get Firestore database")
                return
            
            # Reference to the collection
            collection_ref = db.collection(collection_name)
            
            # Add timestamp for the batch
            batch_timestamp = datetime.now().isoformat()
            
            # Process in smaller batches to avoid timeouts
            batch_size = 100
            total_saved = 0
            
            for i in range(0, len(data_list), batch_size):
                batch = db.batch()
                current_batch = data_list[i:i + batch_size]
                items_added = 0
                
                for data in current_batch:
                    # Add batch timestamp to data
                    data['batch_timestamp'] = batch_timestamp
                    
                    # Use document ID if available, otherwise generate a new one
                    if 'id' in data:
                        doc_ref = collection_ref.document(str(data['id']))
                    else:
                        doc_ref = collection_ref.document()
                    
                    batch.set(doc_ref, data)
                    items_added += 1
                
                # Commit the current batch
                batch.commit()
                total_saved += items_added
                logger.info(f"Committed batch of {items_added} items to Firebase")
            
            logger.info(f"Successfully saved {total_saved} items to Firebase collection '{collection_name}'")
            return
            
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Error saving data to Firebase (attempt {retry_count}/{max_retries}): {str(e)}")
                time.sleep(2 ** retry_count)  # Exponential backoff
            else:
                logger.error(f"Failed to save data to Firebase after {max_retries} attempts: {str(e)}")
                # Save to local file as backup
                backup_file = f"data/{collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                try:
                    with open(backup_file, 'w') as f:
                        json.dump(data_list, f, indent=4)
                    logger.info(f"Saved data to backup file: {backup_file}")
                except Exception as backup_error:
                    logger.error(f"Error saving backup file: {str(backup_error)}")
                return

def query_firebase(collection_name, limit=10, order_by='scraped_at', descending=True):
    """
    Queries data from Firebase Firestore with retries
    
    Args:
        collection_name (str): The name of the collection to query
        limit (int): The maximum number of items to return
        order_by (str): The field to order by
        descending (bool): Whether to order in descending order
    
    Returns:
        list: The list of items retrieved from Firestore
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Initialize Firebase if not already initialized
            if not firebase_app:
                initialize_firebase()
            
            if not firebase_app:
                logger.error("Firebase not initialized, cannot query data")
                return []
            
            # Get Firestore database
            db = get_firestore_db()
            
            if not db:
                logger.error("Could not get Firestore database")
                return []
            
            # Query the collection
            collection_ref = db.collection(collection_name)
            
            # Apply ordering
            if order_by:
                if descending:
                    query = collection_ref.order_by(order_by, direction=firestore.Query.DESCENDING)
                else:
                    query = collection_ref.order_by(order_by)
            else:
                query = collection_ref
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Execute query
            docs = query.get()
            
            # Convert to list of dictionaries
            results = []
            for doc in docs:
                item = doc.to_dict()
                item['doc_id'] = doc.id
                results.append(item)
            
            logger.info(f"Successfully queried {len(results)} items from Firebase collection '{collection_name}'")
            return results
            
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Error querying data from Firebase (attempt {retry_count}/{max_retries}): {str(e)}")
                time.sleep(2 ** retry_count)  # Exponential backoff
            else:
                logger.error(f"Failed to query data from Firebase after {max_retries} attempts: {str(e)}")
                return []
