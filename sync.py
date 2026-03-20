from conn import model,index

def sync_to_cloud(category, name, price, unit, img_url,market):
    # Create a unique ID
    prod_id = f"{category.lower().replace(' ', '-')}-{name.lower().replace(' ', '-')}"
    
    # A. Push to Supabase (Every day = New Row)
    # This builds your history for ML Regressions
    # supabase.table("price_history").insert({
    #     "prod_id": prod_id,
    #     "name": name,
    #     "price": price,
    #     "category": category
    # }).execute()

    # B. Push to Pinecone (Every day = Overwrite/Update)
    # This keeps your search index fresh
    vector = model.encode(f"{name} {category}").tolist()
    
    index.upsert(vectors=[{
        "id": prod_id,
        "values": vector,
        "metadata": {
            "name": name,
            "current_price": price,
            "unit": unit,
            "image_url": img_url,
            "market": market
        }
    }])
    
    print(f"Synced {name} to both databases.")