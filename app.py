import os
from flask import Flask
from flask_restful import Api
from resources import utilities
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
#from resources.osc import OscAPI
from resources.places import PlacesAPI
from resources.country import CountryAPI
from resources.easter_egg import EasterEgg

app = Flask(__name__)
api = Api(app)


if __name__ == '__main__':
    print 'Starting up the service.'
    args = utilities.parse_args()
    configs = utilities.get_configs(args)

    print 'Setting up MITIE.'
    ner_model_eng = utilities.setup_mitie(configs['mitie_directory'],
                                      configs['mitie_ner_model'])
    # Need to check here if Spanish is in config
    ner_model_spa = utilities.setup_mitie(configs['mitie_directory'],
                                      configs['mitie_ner_model_spa'])


    print 'Setting up Word2Vec.'
    location = os.path.realpath(os.path.join(os.getcwd(),
                                                 os.path.dirname(__file__)))
    #w2v_data_eng = utilities.setup_w2v(configs['word2vec_model'],
    #                               location + '/resources/stopword_country_names.json',
    #                               w2v_format = "google")

    #
    #country_kwargs_eng = {'ner_model': ner_model_eng,
    #                  'index': w2v_data_eng['index'],
    #                  'vocab_set': w2v_data_eng['vocab_set'],
    #                  'prebuilt': w2v_data_eng['prebuilt'],
    #                  'idx_country_mapping': w2v_data_eng['idx_country_mapping']}
 
    
    try:
        #configs['spanish_word2vec_model']:
        # 'spa' is used instead of the usual 'es' to avoid elasticsearch confusion
        w2v_data_spa = utilities.setup_w2v(configs['word2vec_model_spa'],
                                   # change this to spanish
                                   location + '/resources/stopword_country_names.json',
                                   w2v_format = "gensim")
        country_kwargs_spa = {'ner_model': ner_model_spa,
                      'index': w2v_data_spa['index'],
                      'vocab_set': w2v_data_spa['vocab_set'],
                      'prebuilt': w2v_data_spa['prebuilt'],
                      'idx_country_mapping': w2v_data_spa['idx_country_mapping']}
    except KeyError:
        pass


    print 'Setting up Elasticsearch connection.'
    es_conn = utilities.setup_es(configs['es_host'], configs['es_port'])

    api.add_resource(PlacesAPI,
                     '/places',
                     resource_class_kwargs={'ner_model': ner_model,
                                            'es_conn': es_conn,
                                            'country_kwargs': country_kwargs})
    #api.add_resource(CountryAPI, '/country',
    #                 resource_class_kwargs=country_kwargs_eng)
    api.add_resource(CountryAPI, '/country_spa',
                     resource_class_kwargs=country_kwargs_spa)
    api.add_resource(EasterEgg, '/easter_egg')

    print 'Starting server.'
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(configs['mordecai_port'])
    IOLoop.instance().start()
