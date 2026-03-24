from conn import model,index,supabase
import re
from datetime import date
def sync_to_cloud(category, name, price, unit,quantity, img_url,market):
    # Create a unique ID
    prod_id = f"{category.lower().replace(' ', '-')}-{name.lower().replace(' ', '-')}-{market}"

    prod_id = prod_id.encode("ascii", "ignore").decode("ascii")
    
    # Also good practice to remove any other weird symbols using Regex
    prod_id = re.sub(r'[^a-zA-Z0-9-]', '', prod_id)

    vector = model.encode(f"{name} {category}").tolist()

    yesterday_price = None
    try:
        existing_data = index.fetch(ids=[prod_id])
        if prod_id in existing_data['vectors']:
            # Move the old "current" to "yesterday"
            yesterday_price = existing_data['vectors'][prod_id]['metadata'].get('current_price')
    except Exception as e:
        print(f"Could not fetch old data for {name}: {e}")
    
    index.upsert(vectors=[{
        "id": prod_id,
        "values": vector,
        "metadata": {
            "name": name,
            "current_price": price,
            "unit": unit,
            "quantity": quantity,
            "image_url": img_url,
            "market": market,
            "yesterday_price": yesterday_price if yesterday_price else price,
        }
    }])

    product_data = {"prod_id":prod_id,"price":price,"date":date.today().isoformat()}


    supabase.table("products_history").insert(
        product_data
    ).execute()
    
    print(f"Synced {name} to both databases.")


