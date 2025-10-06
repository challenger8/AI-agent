# Create a test file to see what's happening
import logging
logging.basicConfig(level=logging.DEBUG)

from database.database import create_database_manager
from models.repositories import create_repositories
from models.deal_model import Deal
from datetime import datetime
import uuid

db = create_database_manager()
repos = create_repositories(db)

# Try to create a deal
deal = Deal(
    Id=str(uuid.uuid4()),
    Title="Test Deal Debug",
    Description="Testing",
    RegisterTime=datetime.now(),
    Price=1000,
    Status="Open"
)

print(f"Creating deal with ID: {deal.Id}")
result = repos.deals.create_deal(deal)
print(f"Result: {result}")

if result:
    # Try to retrieve it
    retrieved = repos.deals.get_deal_by_id(result)
    print(f"Retrieved: {retrieved}")
else:
    print("❌ Create failed - check logs above for error")
