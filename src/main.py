# Opencensus Azure imports
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace.span import SpanKind
from opencensus.trace.status import Status
from opencensus.trace import config_integration
from opencensus.ext.azure.log_exporter import AzureLogHandler

#FastAPI & Other imports 
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from datetime import datetime
import logging, time, os, uvicorn
from pydantic import BaseModel

# Metric imports
from opencensus.ext.azure import metrics_exporter
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module

logger = logging.getLogger(__name__)

app = FastAPI()

club_db = []

class Club(BaseModel):
    name: str
    country: str
    established: int

# load en vars
load_dotenv()

# get instrumentation key 
APPINSIGHTS_INSTRUMENTATIONKEY = os.environ["APPINSIGHTS_INSTRUMENTATIONKEY"]

HTTP_URL = COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

@app.on_event("startup")
async def startup_event():
    print('using temporary directory:')
    config_integration.trace_integrations(['logging'])
    logger = logging.getLogger(__name__)

    handler = AzureLogHandler(connection_string=f'InstrumentationKey={APPINSIGHTS_INSTRUMENTATIONKEY}')
    logger.addHandler(handler)

@app.on_event('shutdown')
async def shutdown_event():
    await get_http_client_session().close()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    tracer = Tracer(exporter=AzureExporter(connection_string=f'InstrumentationKey={APPINSIGHTS_INSTRUMENTATIONKEY}'),sampler=ProbabilitySampler(1.0))
    with tracer.span("main") as span:
        span.span_kind = SpanKind.SERVER
            
        response = await call_next(request)

        tracer.add_attribute_to_current_span(
                attribute_key=HTTP_STATUS_CODE,
                attribute_value=response.status_code)
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_URL,
            attribute_value=str(request.url))
        
    return response

@app.get("/")
async def root(request:Request):
    message="Clubs API"
    print(message)
    logger.warning(message)
    return message

# Create Club details
@app.post('/clubs')
def create_club(club:Club):
    message="creating club"
    print(message)
    logger.info(message)

    try:
        # This is scenario to throw an error in code when you provide 0 as established date
        print(1/club.established)

        # Append club
        club_db.append(club.dict())

        ## CustomDimensions
        properties = {'custom_dimensions': club_db[-1] }
        print(properties)
        logger.warning('club record is added', extra=properties)
        
        return club_db[-1]
    except:
        # log exception when there's an error
        error_message = "An error occured while creating club"
        logger.error(error_message)
        logger.exception(error_message)
        return error_message

# Get All Clubs
@app.get('/clubs')
def get_clubs():
    message="get all clubs"
    print(message)
    logger.info(message)
    return club_db

# Delete a club
@app.delete('/clubs/{club_name}')
def delete_club(club_name: str):
    message="deleting club"
    print(message)
    logger.info(message)
    # find club index by club name
    club_index = [i for i,x in enumerate(club_db) if x['name'] == club_name]
    try:
        club_db.pop(club_index[0])
        logger.warning(f'club record is deleted id:{club_index}, {club_name}')
        return club_db
    except:
        # log exception when there's an error
        logger.exception(f'An error occured while deleting club id:{club_index}, {club_name}')
        return f'An error occured while deleting club id:{club_index}, {club_name}'

# Generate some custom metrics
@app.get("/log_custom_metric")
async def log_custom_metric():
    stats = stats_module.stats
    view_manager = stats.view_manager
    stats_recorder = stats.stats_recorder

    loop_measure = measure_module.MeasureInt("loop", "number of loop", "loop")
    loop_view = view_module.View("metric name: club stats", "number of loop", [], loop_measure, aggregation_module.CountAggregation())
    view_manager.register_view(loop_view)
    mmap = stats_recorder.new_measurement_map()
    tmap = tag_map_module.TagMap()

    for i in range(1,3):
        mmap.measure_int_put(loop_measure, 1)
        mmap.record(tmap)
        metrics = list(mmap.measure_to_view_map.get_metrics(datetime.utcnow()))
        print(metrics[0].time_series[0].points[0])

    exporter = metrics_exporter.new_metrics_exporter(
        connection_string=f'InstrumentationKey={APPINSIGHTS_INSTRUMENTATIONKEY}')

    view_manager.register_exporter(exporter)
    return "Log custom metric"


if __name__=="__main__":
    print("main started")
    uvicorn.run("main:app", port=8000, log_level="info")