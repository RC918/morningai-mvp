cd /opt/render/project/src/apps/api
echo "Current working directory: $(pwd)"
export PYTHONPATH=$(pwd)
echo "Updated PYTHONPATH: $PYTHONPATH"
rm -f src/database/app.db
mkdir -p src/database
python3.11 -c "import sys; print(sys.path); from database import Base, engine; Base.metadata.create_all(engine)"


