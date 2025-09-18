rm -f /app/src/database/app.db
mkdir -p /app/src/database
python -c "from src.database import Base, engine; Base.metadata.create_all(engine)"

