## install
cd corese/
mvn -Dmaven.test.skip=true package

## prepare environment
# start corese with linked function support
java -jar corese/corese-server/target/corese-server-4.1.1-jar-with-dependencies.jar -lf

# start dynamic gui backend
cd dynamic_gui_backend
export FLASK_APP=simple_server.py
python -m flask run

# create UI for TD
python UserInterfaceGenerator.py