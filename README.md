[![Circle CI](https://circleci.com/gh/caerusassociates/mordecai.svg?style=svg)](https://circleci.com/gh/caerusassociates/mordecai)

mordecai
=========

Custom-built full text geoparsing. Extract all the place names from a piece of
text, resolve them to the correct place, and return their coordinates and
structured geographic information.

This software was donated to the Open Event Data Alliance by Caerus Associates.
See [Releases](https://github.com/openeventdata/mordecai/releases) for the
2015-2016 production version of Mordecai.

Why Mordecai?
------------

Mordecai was developed to address several specific needs that previous text
geoparsing software did not. These specific requirements include:

- Overcoming a strong preference for US locations in existing geoparsing
  software. Mordecai makes determining the country focus of the text should
  be a separate and accurate step in the geoparsing process.
- Ease of setup and use. The system should be installable and usable by people
  with only basic programming skills. Mordecai does this by running as a Docker
  + REST service, hiding the complexity of installation from end users.
- Ease of modification. This software was developed to be used primarily by
  social science researchers, who tend to be much more familiar with Python
  than Java. Mordecai makes the key steps in the geoparsing process (named entity
  extraction, place name resolution, gazetteer lookup) exposed and easily
  changed.
- Language-agnostic architecture. The only language-specific components of
  Mordecai are the named entity extraction model and the word2vec model. Both
  of these can be easily swapped out, giving researchers the ability to
  geoparse non-English text, which is a capability that has not existed in open
  source software until now.

How does it work?
-----------------

`Mordecai` accepts text and returns structured geographic information extracted
from it. It does this in several ways:

- It uses [MITIE](https://github.com/mit-nlp/MITIE) named entity recognition to
  extract placenames from the text. In the default configuration, it uses the
  out-of-the-box MITIE models, but these can be changed out for custom models
  when needed.

- It uses [word2vec](https://code.google.com/p/word2vec/)'s models, with
  [gensim](https://radimrehurek.com/gensim/)'s Python implementation, to infer
  the country focus of an article given the word vectors of the article's
  placenames.  The word2vec vectors of all the place names extracted from the
  text are averaged, and this average vector is compared to the vectors for all
  country names. The closest country is used as the focus country of the piece of
  text.

- It uses a country-filtered search of the [geonames](http://www.geonames.org/)
  gazetteer in [Elasticsearch](https://www.elastic.co/products/elasticsearch)
  (with some custom logic) to find the latitude and longitude for each place
  mentioned in the text.

It runs as a Flask-RESTful service inside a Docker container.

Simple Installation
------------

Mordecai is built as a series of [Docker](https://www.docker.com/) containers,
which means that you won't need to install any software except Docker to use
it. You can find instructions for installing Docker on your operating system
[here](https://docs.docker.com/engine/installation/).

To start Mordecai locally, run these four commands:

```
sudo docker pull openeventdata/es-geonames
sudo docker run -d -p 9200:9200 --name=elastic openeventdata/es-geonames
sudo docker build -t mordecai .
sudo docker run -d -p 5000:5000 --link elastic:elastic mordecai
```

### Explanation:

The first line downloads a pre-built image of a Geonames Elasticsearch
container. This container holds the geographic gazetteer that Mordecai uses to
associate place names with latitudes and longitudes.

Line 2 starts that container running locally on port 9200 with the name `elastic`.

Line 3 builds the main Mordecai image using the commands in the `Dockerfile`. 

Line 4 starts the Mordecai container and tells it to connect to our already
running `elastic` container with the `--link elastic:elastic` option.. Mordecai
will be accessible on port 5000. By default, Docker runs on 0.0.0.0, so any
machine on your network will be able to access it.

**NOTE**: Many of the required components for `mordecai`, including the
word2vec and MITIE models, are very large so downloading and starting the
service takes a while. You should also ensure that you have approximately 16
gigs of RAM available.


Advanced Configuration
-----------------------

`Mordecai`'s Geonames gazeteer can either be run locally alongside Mordecai or
on a remote server. Elasticsearch/Geonames requires a large amount of memory,
so running it locally may be okay for small projects (if your machine has
enough RAM), but is not recommended for production. 

If you're running elasticsearch/geonames on a different server, you'll need to
make two change:

First, the config file's default settings assume that `es-geonames` is running
locally. If you're running it on a separate server, uncomment and change the
`Server` section of the config file and update with the IP and port of your
running geonames/elasticsearch index.

Second, leave out the `--link elastic:elastic` portion when you call `docker
run` on Mordecai.

Endpoints
---------

1. `/country`

    In: text

    Out: An ISO country code that best matches the country focus of the text (used as input to later searches). In the future, this will be a list of country codes.

2. `/places`

    In: text, country code

    Out: list of dictionaries of placenames and lat/lon in text. The keys are "lat", "lon", "placename", "searchterm", "admin1", and "countrycode". 


4. `/osc`

    In: text

    Out: placenames and lat/lon, customized for OSC stories

Example usage
-------------

```
curl -XPOST -H "Content-Type: application/json"  --data '{"text":"(Reuters) - The Iraqi government claimed victory over Islamic State insurgents in Tikrit on Wednesday after a month-long battle for the city supported by Shiite militiamen and U.S.-led air strikes, saying that only small pockets of resistance remained. State television showed Prime Minister Haidar al-Abadi, accompanied by leaders of the army and police, the provincial governor and Shiite paramilitary leaders, parading through Tikrit and raising an Iraqi flag. The militants captured the city, about 140 km (90 miles) north of Baghdad, last June as they swept through most of Iraqs Sunni Muslim territories, swatting aside a demoralized and disorganized army that has now required an uneasy combination of Iranian and American support to get back on its feet."}' 'http://localhost:5000/places'
```

Or if you know this text is about Iraq:

```
curl -XPOST -H "Content-Type: application/json"  --data '{"text":"(Reuters) - The Iraqi government claimed victory over Islamic State insurgents in Tikrit on Wednesday after a month-long battle for the city supported by Shiite militiamen and U.S.-led air strikes, saying that only small pockets of resistance remained. State television showed Prime Minister Haidar al-Abadi, accompanied by leaders of the army and police, the provincial governor and Shiite paramilitary leaders, parading through Tikrit and raising an Iraqi flag. The militants captured the city, about 140 km (90 miles) north of Baghdad, last June as they swept through most of Iraqs Sunni Muslim territories, swatting aside a demoralized and disorganized army that has now required an uneasy combination of Iranian and American support to get back on its feet.", "country": "IRQ"}' 'http://localhost:5000/places'
```

Returns:
`[{"lat": 34.61581, "placename": "Tikrit", "seachterm": "Tikrit", "lon": 43.67861, "countrycode": "IRQ"}, {"lat": 34.61581, "placename": "Tikrit", "seachterm": "Tikrit", "lon": 43.67861, "countrycode": "IRQ"}, {"lat": 33.32475, "placename": "Baghdad", "seachterm": "Baghdad", "lon": 44.42129, "countrycode": "IRQ"}]`

###Python

```
import json
import requests

headers = {'Content-Type': 'application/json'}
data = {'text': """(Reuters) - The Iraqi government claimed victory over Islamic State insurgents in Tikrit on Wednesday after a month-long battle for the city supported by Shiite militiamen and U.S.-led air strikes, saying that only small pockets of resistance remained. State television showed Prime Minister Haidar al-Abadi, accompanied by leaders of the army and police, the provincial governor and Shiite paramilitary leaders, parading through Tikrit and raising an Iraqi flag. The militants captured the city, about 140 km (90 miles) north of Baghdad, last June as they swept through most of Iraqs Sunni Muslim territories, swatting aside a demoralized and disorganized army that has now required an uneasy combination of Iranian and American support to get back on its feet."""}
data = json.dumps(data)
out = requests.post('http://localhost:5000/places', data=data, headers=headers)
```

Customization
------------

Mordecai is meant to be easy to customize. There are a few ways to do this.

1. Change the MITIE named entity recognition model. This is a matter of changing one line in the configuration file, assuming that the custom trained MITIE model returns entities tagged as "LOCATION".

2. Custom place-picking logic. See the `/osc` for an example. Prior knowledge about the place text is about and the vocabulary used in the text to describe place times can be hard coded into a special endpoint for a particular corpus.

3. If a corpus is known to be about a specific country, that country can be passed to `places` to limit the search to places in that country.

Tests
-----

`mordecai` currently includes a few unit tests. To run the tests:

```
cd resources
py.test
```

The tests currently require access to a running Elastic/Geonames service to
complete. If this service is running locally in a Docker container, uncomment
the `Server` section in the config file so host = `localhost` and port =
`9200`.

Contributing
------------

Contributions via pull requests are welcome. Please make sure that changes
pass the unit tests. Any bugs and problems can be reported
on the repo's [issues page](https://github.com/openeventdata/mordecai/issues).

