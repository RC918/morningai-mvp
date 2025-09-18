cd /app/apps/api
export PYTHONPATH=$PYTHONPATH:.
rm -f src/database/app.db
mkdir -p src/database
python3.11 -c "from src.database import Base, engine; Base.metadata.create_all(engine)"

