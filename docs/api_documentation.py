"""
docs/api_documentation.py
-------------------------
API documentation for MoE system
Generates OpenAPI-style documentation
"""

from typing import Any, Dict, List


def get_api_documentation() -> Dict[str, Any]:
    """
    Get OpenAPI-style documentation for MoE system

    Returns:
        API documentation dictionary
    """
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Persian Deal Analyzer - MoE API",
            "description": "Mixture of Experts API for intelligent query routing and processing",
            "version": "1.0.0",
            "contact": {
                "name": "API Support"
            }
        },
        "servers": [
            {
                "url": "http://localhost:8000",
                "description": "Local development server"
            }
        ],
        "paths": {
            "/moe/query": {
                "post": {
                    "summary": "Process query through MoE system",
                    "description": "Routes query to appropriate experts and returns combined results",
                    "operationId": "moeQuery",
                    "tags": ["MoE"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/QueryRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful query processing",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/EnsembleResult"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid request"
                        },
                        "500": {
                            "description": "Server error"
                        }
                    }
                }
            },
            "/moe/batch": {
                "post": {
                    "summary": "Process multiple queries in batch",
                    "description": "Process multiple queries efficiently through the MoE system",
                    "operationId": "moeBatch",
                    "tags": ["MoE"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/BatchQueryRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Batch processing results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/EnsembleResult"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/moe/route": {
                "post": {
                    "summary": "Route query to experts",
                    "description": "Get routing decision without executing experts",
                    "operationId": "moeRoute",
                    "tags": ["Routing"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/QueryRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Routing decision",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/RoutingDecision"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/moe/experts": {
                "get": {
                    "summary": "List available experts",
                    "description": "Get list of all available expert types and their configurations",
                    "operationId": "listExperts",
                    "tags": ["Experts"],
                    "responses": {
                        "200": {
                            "description": "List of experts",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/ExpertInfo"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/moe/experts/{expert_type}": {
                "post": {
                    "summary": "Query specific expert",
                    "description": "Send query directly to a specific expert",
                    "operationId": "queryExpert",
                    "tags": ["Experts"],
                    "parameters": [
                        {
                            "name": "expert_type",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string",
                                "enum": ["deal_analysis", "sentiment", "activity", "risk_assessment", "search"]
                            }
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/QueryRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Expert result",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ExpertResult"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/moe/metrics": {
                "get": {
                    "summary": "Get performance metrics",
                    "description": "Get current performance metrics and statistics",
                    "operationId": "getMetrics",
                    "tags": ["Monitoring"],
                    "responses": {
                        "200": {
                            "description": "Performance metrics",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/DashboardData"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/moe/cache/stats": {
                "get": {
                    "summary": "Get cache statistics",
                    "description": "Get current cache statistics",
                    "operationId": "getCacheStats",
                    "tags": ["Cache"],
                    "responses": {
                        "200": {
                            "description": "Cache statistics"
                        }
                    }
                }
            },
            "/moe/cache/clear": {
                "post": {
                    "summary": "Clear cache",
                    "description": "Clear all cached results",
                    "operationId": "clearCache",
                    "tags": ["Cache"],
                    "responses": {
                        "200": {
                            "description": "Cache cleared"
                        }
                    }
                }
            },
            "/moe/feedback": {
                "post": {
                    "summary": "Submit feedback",
                    "description": "Submit feedback for a query to improve routing",
                    "operationId": "submitFeedback",
                    "tags": ["Feedback"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/FeedbackRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Feedback recorded"
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "QueryRequest": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Input query text (Persian or English)"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context for routing",
                            "properties": {
                                "expert_hint": {
                                    "type": "string",
                                    "description": "Hint for preferred expert"
                                },
                                "entity_type": {
                                    "type": "string",
                                    "description": "Type of entity being queried"
                                },
                                "deal_id": {
                                    "type": "integer",
                                    "description": "Specific deal ID"
                                }
                            }
                        }
                    }
                },
                "BatchQueryRequest": {
                    "type": "object",
                    "required": ["queries"],
                    "properties": {
                        "queries": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/QueryRequest"
                            },
                            "description": "List of queries to process"
                        },
                        "parallel": {
                            "type": "boolean",
                            "default": True,
                            "description": "Process queries in parallel"
                        }
                    }
                },
                "EnsembleResult": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string"
                        },
                        "combined_data": {
                            "type": "object",
                            "description": "Combined results from all experts"
                        },
                        "expert_contributions": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/ExpertContribution"
                            }
                        },
                        "overall_confidence": {
                            "type": "number",
                            "format": "float"
                        },
                        "strategy_used": {
                            "type": "string"
                        },
                        "total_execution_time_ms": {
                            "type": "number"
                        }
                    }
                },
                "ExpertResult": {
                    "type": "object",
                    "properties": {
                        "expert_type": {
                            "type": "string"
                        },
                        "success": {
                            "type": "boolean"
                        },
                        "data": {
                            "type": "object"
                        },
                        "confidence": {
                            "type": "number"
                        },
                        "reasoning": {
                            "type": "string"
                        },
                        "execution_time_ms": {
                            "type": "number"
                        }
                    }
                },
                "ExpertContribution": {
                    "type": "object",
                    "properties": {
                        "expert_type": {
                            "type": "string"
                        },
                        "weight": {
                            "type": "number"
                        },
                        "confidence": {
                            "type": "number"
                        }
                    }
                },
                "RoutingDecision": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string"
                        },
                        "selected_experts": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "confidence_scores": {
                            "type": "object"
                        },
                        "query_type": {
                            "type": "string"
                        },
                        "reasoning": {
                            "type": "string"
                        }
                    }
                },
                "ExpertInfo": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string"
                        },
                        "description": {
                            "type": "string"
                        },
                        "keywords": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "timeout": {
                            "type": "integer"
                        },
                        "threshold": {
                            "type": "number"
                        }
                    }
                },
                "DashboardData": {
                    "type": "object",
                    "properties": {
                        "system": {
                            "type": "object"
                        },
                        "experts": {
                            "type": "object"
                        },
                        "recent_queries": {
                            "type": "array"
                        }
                    }
                },
                "FeedbackRequest": {
                    "type": "object",
                    "required": ["query_id", "rating"],
                    "properties": {
                        "query_id": {
                            "type": "string"
                        },
                        "rating": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 5
                        },
                        "correct_expert": {
                            "type": "string",
                            "description": "Expert that should have been used"
                        },
                        "comments": {
                            "type": "string"
                        }
                    }
                }
            }
        },
        "tags": [
            {
                "name": "MoE",
                "description": "Mixture of Experts query processing"
            },
            {
                "name": "Routing",
                "description": "Query routing operations"
            },
            {
                "name": "Experts",
                "description": "Expert management"
            },
            {
                "name": "Monitoring",
                "description": "Performance monitoring"
            },
            {
                "name": "Cache",
                "description": "Cache management"
            },
            {
                "name": "Feedback",
                "description": "Feedback and learning"
            }
        ]
    }


def generate_markdown_docs() -> str:
    """
    Generate markdown documentation

    Returns:
        Markdown formatted documentation
    """
    docs = get_api_documentation()

    lines = [
        "# MoE API Documentation",
        "",
        f"**Version**: {docs['info']['version']}",
        "",
        docs['info']['description'],
        "",
        "## Endpoints",
        ""
    ]

    for path, methods in docs['paths'].items():
        for method, details in methods.items():
            lines.extend([
                f"### {method.upper()} {path}",
                "",
                f"**{details['summary']}**",
                "",
                details['description'],
                "",
                f"Tags: {', '.join(details.get('tags', []))}",
                ""
            ])

    lines.extend([
        "## Schemas",
        ""
    ])

    for name, schema in docs['components']['schemas'].items():
        lines.extend([
            f"### {name}",
            "",
            f"Type: {schema['type']}",
            ""
        ])

        if 'properties' in schema:
            lines.append("Properties:")
            for prop_name, prop_details in schema['properties'].items():
                desc = prop_details.get('description', '')
                prop_type = prop_details.get('type', 'object')
                lines.append(f"- `{prop_name}` ({prop_type}): {desc}")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import json
    print(json.dumps(get_api_documentation(), indent=2))
