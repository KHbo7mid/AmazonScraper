import psycopg2
from psycopg2.extras import RealDictCursor
import logging 
from contextlib import contextmanager
import os
from typing import List ,Dict,Optional
from dotenv import load_dotenv
from app.utils.logger import setup_logger
load_dotenv()

class DBManager:
    def __init__(self):
        self.connection_params={
            'host': os.getenv('DB_HOST'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'port': os.getenv('DB_PORT')
        }
        self.logger = setup_logger(__name__)
        
    @contextmanager
    def get_connection(self):
        """Context manager for database connection"""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            self.logger.info("Database connection established successfully.")
            yield conn
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
                
    @contextmanager
    def get_cursor(self,connection=None):
        """Context manager for database cursor"""
        if connection :
            cursor=connection.cursor()
            try:
                yield cursor
                connection.commit()
                self.logger.info("Transaction committed successfully.")
            except Exception as e:
                connection.rollback()
                self.logger.error(f"Cursor error: {e}")
                raise
            finally:
                cursor.close()
        else:
            #create new connection and cursor
            with self.get_connection() as conn:
                cursor=conn.cursor()
                try:
                    yield cursor
                    conn.commit()
                    self.logger.info("Transaction committed successfully.")
                except Exception as e:
                    conn.rollback()
                    self.logger.error(f"Cursor error: {e}")
                    raise
                finally:
                    cursor.close()
                    
    # Add this method to your DBManager class
    def create_tables(self):
        """Create the necessary tables for the Amazon scraper"""
        create_tables = """
        CREATE TABLE IF NOT EXISTS categories(
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            url TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS products(
            id SERIAL PRIMARY KEY,
            category_id INTEGER REFERENCES categories(id),
            title TEXT NOT NULL,
            brand VARCHAR(255),
            price DECIMAL(10,2),
            original_price DECIMAL(10,2),
            discount_percent DECIMAL(5,2),
            rating DECIMAL(3,2),
            reviews_count INTEGER DEFAULT 0,
            product_link TEXT UNIQUE NOT NULL,
            image_url TEXT,
            availability VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        try:
            self.execute_query(create_tables)
            self.logger.info("Database tables created successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            return False
                    
    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Dict]]:
        """Execute a query and return results if any"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                return None
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
        
    def insert_category(self, name: str, url: str) -> int:
        """Insert a new category and return its ID, skip if exists"""
        
        check_query = "SELECT id FROM categories WHERE name = %s OR url = %s;"
        
        try:
            with self.get_cursor() as cursor:
                # Check for existing category
                cursor.execute(check_query, (name, url))
                existing = cursor.fetchone()
                
                if existing:
                    self.logger.info(f"Category '{name}' already exists with ID {existing[0]}")
                    return existing[0]
                
                # Insert new category
                insert_query = "INSERT INTO categories (name, url) VALUES (%s, %s) RETURNING id;"
                cursor.execute(insert_query, (name, url))
                category_id = cursor.fetchone()[0]
                self.logger.info(f"Inserted category '{name}' with ID {category_id}")
                return category_id
                
        except Exception as e:
            self.logger.error(f"Failed to insert category: {e}")
            raise
        
        
    def insert_product(self, product_data: Dict) -> int:
        """Insert a new product and return its ID, handle duplicates by URL"""
       
        check_query = "SELECT id FROM products WHERE title = %s AND product_link = %s;"
        
        try:
            with self.get_cursor() as cursor:
                
                cursor.execute(check_query, (product_data['title'], product_data['product_link']))
                existing = cursor.fetchone()
                
                if existing:
                    self.logger.info(f"Product '{product_data['title']}' already exists with ID {existing[0]}")
                    return existing[0]
                
                
                insert_query = """
                INSERT INTO products (
                    category_id, title, brand, price, original_price, 
                    discount_percent, rating, reviews_count, product_link, 
                    image_url, availability
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_link) 
                DO UPDATE SET
                    price = EXCLUDED.price,
                    original_price = EXCLUDED.original_price,
                    discount_percent = EXCLUDED.discount_percent,
                    rating = EXCLUDED.rating,
                    availability = EXCLUDED.availability,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """
                cursor.execute(insert_query, (
                    product_data['category_id'],
                    product_data['title'],
                    product_data.get('brand'),
                    product_data.get('price'),
                    product_data.get('original_price'),
                    product_data.get('discount_percent', 0),
                    product_data.get('rating'),
                    product_data.get('reviews_count', 0),
                    product_data['product_link'],
                    product_data.get('image_url'),
                    product_data.get('availability', False)
                ))
                product_id = cursor.fetchone()[0]
                self.logger.info(f"Inserted/Updated product '{product_data['title']}' (ID: {product_id})")
                return product_id
                
        except Exception as e:
            self.logger.error(f"Failed to insert product: {e}")
            raise
        
    def get_all_categories(self) -> List[Dict]:
        """Get all categories from database"""
        query = "SELECT id, name, url FROM categories;"
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                categories = []
                for row in results:
                    categories.append({
                        'id': row[0],
                        'name': row[1],
                        'url': row[2]
                    })
                return categories
        except Exception as e:
            self.logger.error(f"Failed to get categories: {e}")
            return []