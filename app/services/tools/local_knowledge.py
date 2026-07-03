"""
Tool: search_local_knowledge
Searches unstructured local information via vector similarity.

Prototype: returns dummy chunks.
Phase 1: query a real vector store (pgvector, Chroma, Pinecone...) with embeddings.
"""
import json

SCHEMA = {
    'name': 'search_local_knowledge',
    'description': (
        'Search unstructured local information: town history, practical info, '
        'local tips, PDF guides, municipal web content. '
        'Use this for questions the other tools do not cover '
        '(parking, opening hours, transport, local services, etc.).'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'Semantic search query, e.g. "on aparcar a Berga"',
            },
            'location': {
                'type': 'string',
                'description': 'Location context, e.g. "Berga"',
            },
        },
        'required': ['query'],
    },
}

_DUMMY_CHUNKS = [
    {
        'source':  'Guia Turística de Berga 2024 (PDF)',
        'page':    3,
        'summary': 'Història de Berga: fundada al s. IX, capital del Berguedà des del s. XIII. '
                   'Coneguda per La Patum, declarada Patrimoni de la Humanitat.',
    },
    {
        'source':  'Web Ajuntament de Berga',
        'page':    None,
        'summary': 'Aparcament gratuït al Passeig de la Pau i al Parc de les Fonts. '
                   'Zona blava al centre (1,20€/hora). Aparcament municipal obert 24h al carrer Montserrat.',
    },
    {
        'source':  'Oficina de Turisme del Berguedà',
        'page':    None,
        'summary': 'Horaris Oficina Turisme: Dilluns-Divendres 9-14h i 16-19h, '
                   'Dissabtes 10-14h i 16-19h, Diumenges 10-14h. '
                   'Tel: 938 210 384. Adreça: Plaça de la Creu 1, Berga.',
    },
    {
        'source':  'Guia de Senderisme Berguedà (PDF)',
        'page':    12,
        'summary': 'Transport públic: Bus L4 Barcelona-Berga cada hora. '
                   'Durada aproximada 1h 30min. Preu ~10€. '
                   'Bus local a Bagà, Gironella i Puig-reig des de Berga.',
    },
    {
        'source':  'Web Femturisme.cat',
        'page':    None,
        'summary': 'Restaurants recomanats a Berga: Can Font (cuina de mercat), '
                   'L\'Àpat (menú degustació), Bar La Plaça (tapes i entrepans). '
                   'Mercat setmanal: dimarts matí a la Plaça de Sant Pere.',
    },
]


def execute(tool_input: dict) -> str:
    query    = tool_input.get('query', '')
    location = tool_input.get('location', 'Berguedà')

    # Phase 1: embed `query`, run similarity search, return top-k chunks
    # Example with pgvector:
    #   embedding = embed(query)
    #   chunks = db.execute(
    #       "SELECT * FROM documents ORDER BY embedding <-> %s LIMIT 5",
    #       (embedding,)
    #   ).fetchall()

    results = _DUMMY_CHUNKS  # return all dummy chunks for now

    return json.dumps({
        'query':    query,
        'location': location,
        'total':    len(results),
        'results':  results,
    })
