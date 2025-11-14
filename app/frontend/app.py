import streamlit as st
import requests
from typing import Dict, Any
import pandas as pd

API_URL = "http://localhost:8000/api"

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(page_title="Amazon Best Deals", page_icon="🔥", layout="wide")

# -------------------------
# TOP BAR
# -------------------------
st.markdown(
    """
    <style>
        .title-box {
            background: linear-gradient(90deg, #ff9900, #ff5e00);
            padding: 20px;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
            font-size: 28px;
            font-weight: bold;
        }
        .product-card {
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #dddddd;
            background: #ffffff;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            margin-bottom: 15px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title-box">🛒 Amazon Best Deals Explorer</div>', unsafe_allow_html=True)



st.markdown("### Srape New Products")

col_scrape = st.columns([1, 4])[0]

with col_scrape:
    if st.button("🔄 Scrape Products Now", use_container_width=True):
        try:
            resp = requests.post(f"{API_URL}/scrape")
            resp.raise_for_status()
            st.success("✅ Scraping started successfully!")
        except Exception as e:
            st.error(f"❌ Error starting scraping: {e}")



def display_product_card(product: Dict[str, Any]):
    st.markdown('<div class="product-card">', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(product.get('image_url', "https://via.placeholder.com/150"), width=150)

    with col2:
        st.subheader(product['title'])

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.write(f"💰 **${product['price']:.2f}**")
            if product.get('original_price'):
                st.write(f"~~${product['original_price']:.2f}~~")

        with col_p2:
            if product.get("discount_percent", 0) > 0:
                st.write(f"🔥 **{product['discount_percent']}% OFF**")

        with col_p3:
            if product.get("rating"):
                st.write(f"⭐ {product['rating']} ({product.get('reviews_count', 0)} reviews)")

        st.write(f"**Brand:** {product.get('brand', 'N/A')}")
        st.write(f"**Category:** {product.get('category_name', 'N/A')}")
        st.write(f"**Availability:** {product.get('availability', 'N/A')}")

        st.markdown(f"[🔗 View on Amazon]({product['product_link']})")

    st.markdown("</div>", unsafe_allow_html=True)




def load_categories():
    try:
        res = requests.get(f"{API_URL}/categories")
        res.raise_for_status()
        cats = res.json()
        return {c["name"]: c["id"] for c in cats}
    except:
        return {"All": None}

category_options = load_categories()



tab1, tab2 = st.tabs(["🔥 Best Deals", "📦 All Products"])




with tab1:
    st.subheader("🔥 Today's Best Deals")
    num_deals = st.slider("Number of deals to show", 5, 20, 10)

    if st.button("Show Best Deals"):
        try:
            response = requests.get(f"{API_URL}/best-deals?limit={num_deals}")
            response.raise_for_status()
            deals = response.json()

            if not deals:
                st.info("No deals found.")
            else:
                st.success(f"Showing {len(deals)} deals")
                for product in deals:
                    display_product_card(product)

        except Exception as e:
            st.error(f"Error: {e}")




with tab2:
    st.subheader("📦 All Products")

    st.markdown("### 🔍 Filters")

    items_per_page = st.selectbox("Items per page", [10, 20, 50, 100], index=1)
    sort_by = st.selectbox("Sort by", ["id", "price", "rating", "discount_percent"])
    sort_order = st.selectbox("Order", ["ASC", "DESC"])

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        min_price = st.number_input("Min price", 0.0)
    with col_f2:
        max_price = st.number_input("Max price", 0.0)
    with col_f3:
        min_discount = st.number_input("Min discount %", 0.0)
    with col_f4:
        min_rating = st.number_input("Min rating", 0.0)

    col_f5, col_f6 = st.columns(2)
    with col_f5:
        selected_category = st.selectbox("Category", ["All"] + list(category_options.keys()))
    with col_f6:
        selected_brand = st.text_input("Brand (optional)", "")

    if st.button("Load Products"):
        params = {
            "limit": items_per_page,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "page": 1
        }

        if min_price > 0: params["min_price"] = min_price
        if max_price > 0: params["max_price"] = max_price
        if min_discount > 0: params["min_discount"] = min_discount
        if min_rating > 0: params["min_rating"] = min_rating
        if selected_category != "All":
            params["category_id"] = category_options[selected_category]
        if selected_brand.strip():
            params["brand"] = selected_brand.strip()

        try:
            response = requests.get(f"{API_URL}/products", params=params)
            response.raise_for_status()
            data = response.json()

            products = data["products"]

            if not products:
                st.warning("No products found.")
            else:
                st.success(f"Found {data['total']} products")
                for product in products:
                    display_product_card(product)

                st.write(f"Page {data['page']} of {data['total_pages']}")

        except Exception as e:
            st.error(f"Error: {e}")



