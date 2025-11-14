import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from app.utils.logger import setup_logger

load_dotenv()

class DBManager:
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'amazon_deals'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '5432')
        }
        self.logger = setup_logger(__name__)
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            yield conn
        except Exception as e:
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_cursor(self, connection=None):
        if connection:
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                connection.commit()
            except Exception as e:
                connection.rollback()
                self.logger.error(f"Cursor error: {e}")
                raise
            finally:
                cursor.close()
        else:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                try:
                    yield cursor
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    self.logger.error(f"Cursor error: {e}")
                    raise
                finally:
                    cursor.close()
    
    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Dict]]:
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith("SELECT"):
                    return cursor.fetchall()
                return None
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            raise
        
    def insert_product(self, product_data: Dict) -> int:
       
        exist = self.execute_query(
            "SELECT id FROM products WHERE title = %s OR product_link = %s", 
            (product_data.get("title"), product_data.get("product_link"))
        )
        
        if exist:
            self.logger.info(f"Product already exists: {product_data.get('title')}")
            return exist[0]["id"]  
        
        query = """
            INSERT INTO products 
            (title, brand, price, original_price, discount_percent, rating, reviews_count, product_link, image_url, availability, category_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """
        params = (
            product_data.get("title"),
            product_data.get("brand"),
            product_data.get("price"),
            product_data.get("original_price"),
            product_data.get("discount_percent", 0.0),
            product_data.get("rating"),
            product_data.get("reviews_count", 0),
            product_data.get("product_link"),
            product_data.get("image_url"),
            product_data.get("availability"),
            product_data.get("category_id")
        )
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                product_id = cursor.fetchone()["id"]
                self.logger.info(f"Product inserted: {product_data.get('title')} (ID: {product_id})")
                return product_id
        except Exception as e:
            self.logger.error(f"Failed to insert product '{product_data.get('title')}': {e}")
            return None  
        
    def insert_category(self, name: str, url: str) -> int:
        check_query = "SELECT id FROM categories WHERE name = %s OR url = %s;"
        insert_query = "INSERT INTO categories (name, url) VALUES (%s, %s) RETURNING id;"

        try:
            with self.get_cursor() as cursor:
                cursor.execute(check_query, (name, url))
                existing = cursor.fetchone()

                if existing:
                    self.logger.info(f"Category already exists: {name}")
                    return existing["id"]

                cursor.execute(insert_query, (name, url))
                new_id = cursor.fetchone()["id"]
                self.logger.info(f"Category inserted: {name} (ID: {new_id})")
                return new_id

        except Exception as e:
            self.logger.error(f"Category insert failed for '{name}': {e}")
            return None  
            


    def get_all_categories(self) -> List[Dict]:
        try:
            return self.execute_query("SELECT * FROM categories ORDER BY name;") or []
        except:
            return []

    def get_products(
        self, 
        category_id: Optional[int] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_discount: Optional[float] = None,
        min_rating: Optional[float] = None,
        sort_by: str = "id",
        sort_order: str = "DESC",
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """Get products with filtering, sorting and pagination"""
        base_query = """
            SELECT 
                p.*, 
                c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE 1=1
        """
        count_query = """
            SELECT COUNT(*) as total
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE 1=1
        """
        
        conditions = []
        params = []
        
        # Build WHERE conditions
        if category_id:
            conditions.append("p.category_id = %s")
            params.append(category_id)
        if brand:
            conditions.append("LOWER(p.brand) = LOWER(%s)")
            params.append(brand)
        if min_price is not None:
            conditions.append("p.price >= %s")
            params.append(min_price)
        if max_price is not None:
            conditions.append("p.price <= %s")
            params.append(max_price)
        if min_discount is not None:
            conditions.append("p.discount_percent >= %s")
            params.append(min_discount)
        if min_rating is not None:
            conditions.append("p.rating >= %s")
            params.append(min_rating)
        
        # Add conditions to queries
        where_clause = " AND ".join(conditions)
        if where_clause:
            base_query += f" AND {where_clause}"
            count_query += f" AND {where_clause}"
        
        # Validate sort parameters
        valid_sort_columns = ["id", "price", "discount_percent", "rating", "reviews_count"]
        valid_sort_orders = ["ASC", "DESC"]
        
        sort_by = sort_by if sort_by in valid_sort_columns else "id"
        sort_order = sort_order if sort_order in valid_sort_orders else "DESC"
        
        # Add sorting and pagination
        base_query += f" ORDER BY p.{sort_by} {sort_order} LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        try:
            # Get total count
            total_result = self.execute_query(count_query, tuple(params[:-2])) or [{"total": 0}]
            total_count = total_result[0]["total"]
            
            # Get paginated results
            products = self.execute_query(base_query, tuple(params)) or []
            
            return products, total_count
            
        except Exception as e:
            self.logger.error(f"Failed to get products: {e}")
            return [], 0
        
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        query = """
            SELECT 
                p.*, 
                c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s;
        """
        try:
            results = self.execute_query(query, (product_id,))
            if results:
                return results[0]
            return None
        except Exception as e:
            self.logger.error(f"Failed to get product by ID {product_id}: {e}")
            return None

    def get_best_deals(self, limit: int = 10) -> List[Dict]:
        
        query = """
            SELECT 
                p.*, 
                c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.discount_percent > 0 OR p.rating > 0
            ORDER BY p.discount_percent DESC, p.rating DESC
            LIMIT %s;
        """
        try:
            return self.execute_query(query, (limit,)) or []
        except Exception as e:
            self.logger.error(f"Failed to get best deals: {e}")
            return []