import os
from datadog import initialize, DogStatsd

statsd = DogStatsd(max_buffer_size=1)

options = {
    'api_key': os.environ['DATADOG_API_KEY'],
    'app_key': os.environ['DATADOG_APP_KEY']
}

initialize(**options)

