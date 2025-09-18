cd /app/src
rm -f database/app.db
mkdir -p database
python -c "from database import Base, engine; Base.metadata.create_all(engine)"

