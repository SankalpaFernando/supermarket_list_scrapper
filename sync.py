from conn import model,index

def sync_to_cloud(category, name, price, unit, img_url,market):
    # Create a unique ID
    prod_id = f"{category.lower().replace(' ', '-')}-{name.lower().replace(' ', '-')}"

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
            "image_url": img_url,
            "market": market,
            "yesterday_price": yesterday_price if yesterday_price else price,
        }
    }])
    
    print(f"Synced {name} to both databases.")


