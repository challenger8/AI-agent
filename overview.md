# 🗺️ Implementation Roadmap: RAG + STT + MoE

## 📊 Overview

**Total Estimated Time:** 15-21 days (3-4 weeks)  
**Approach:** Iterative - Build, Test, Integrate, Repeat  
**Order:** STT → RAG → MoE (Easiest to Hardest)

---

## 🎯 Phase 1: Speech-to-Text Service (Days 1-4)

**Goal:** Upload audio files, transcribe Persian speech, create deal activities

### Day 1: Setup & Basic STT Service

#### Morning: Environment Setup
**Tasks:**
1. Install dependencies
   ```bash
   pip install openai-whisper transformers accelerate
   pip install soundfile librosa  # Audio processing
   ```

2. Download models
   - Test with whisper-medium first (faster, smaller)
   - Option for whisper-large-v3 later

3. Create service structure
   ```
   services/stt_service.py
   - __init__
   - load_model()
   - transcribe_audio(audio_path)
   - transcribe_batch(audio_paths)
   ```

**Deliverables:**
- ✅ STT dependencies installed
- ✅ Whisper model downloaded
- ✅ Basic service class created

#### Afternoon: Core Transcription Logic
**Tasks:**
1. Implement transcription method
   - Load audio file
   - Run Whisper inference
   - Return transcribed text
   - Handle errors gracefully

2. Add Persian-specific handling
   - Set language="fa" for Whisper
   - Persian text cleanup
   - Handle mixed Persian/English

3. Test with sample audio
   - Record test audio file
   - Verify transcription accuracy
   - Check performance

**Deliverables:**
- ✅ Working transcription function
- ✅ Test audio files transcribed
- ✅ Error handling implemented

---

### Day 2: Repository & Integration

#### Morning: Audio Storage & Repository
**Tasks:**
1. Create audio file storage
   ```
   audio_files/
   ├── uploads/
   ├── processed/
   └── cache/
   ```

2. Create AudioRepository
   ```python
   models/repositories.py (extend)
   - AudioRepository
     - save_audio(file_data, deal_id)
     - get_audio(audio_id)
     - delete_audio(audio_id)
     - link_to_activity(audio_id, activity_id)
   ```

3. Add database table (if needed)
   ```sql
   CREATE TABLE audio_transcriptions (
       id VARCHAR PRIMARY KEY,
       deal_id VARCHAR REFERENCES deals(id),
       activity_id VARCHAR REFERENCES deal_activities(id),
       file_path VARCHAR,
       transcription TEXT,
       model_used VARCHAR,
       confidence FLOAT,
       created_at TIMESTAMP
   );
   ```

**Deliverables:**
- ✅ Audio storage structure
- ✅ AudioRepository implemented
- ✅ Database schema updated

#### Afternoon: Service Integration
**Tasks:**
1. Integrate with DealService
   ```python
   Deal

Service.create_activity_from_audio(audio_file, deal_id)
   ```

2. Add caching for transcriptions
   - Cache by audio file hash
   - Avoid re-transcribing same audio

3. Batch processing support
   - Process multiple files
   - Progress tracking

**Deliverables:**
- ✅ STT integrated with DealService
- ✅ Transcription caching working
- ✅ Batch processing functional

---

### Day 3: MCP Tools & Gradio UI

#### Morning: MCP Tool Creation
**Tasks:**
1. Add STT tools to tool_handlers.py
   ```python
   - transcribe_audio(audio_file_path)
   - transcribe_and_create_activity(audio_file, deal_id)
   - batch_transcribe(audio_files)
   ```

2. Add schemas
   ```python
   mcp_spec/schemas/tool_schemas.py
   - TranscribeAudioInput
   - TranscribeAndCreateActivityInput
   ```

3. Test MCP tools
   - Test tool calls
   - Verify responses
   - Error handling

**Deliverables:**
- ✅ 3 new MCP tools
- ✅ Schemas defined
- ✅ Tools tested

#### Afternoon: Gradio Interface
**Tasks:**
1. Add "Audio Transcription" tab
   - File upload widget
   - Deal selector dropdown
   - Transcribe button
   - Result display area

2. Implement callbacks
   - Handle file upload
   - Call STT service
   - Display transcription
   - Option to create activity

3. Add progress indicators
   - Processing status
   - Estimated time
   - Cancel option

**Deliverables:**
- ✅ New Gradio tab
- ✅ Audio upload working
- ✅ Live transcription display

---

### Day 4: Testing & Optimization

#### Morning: Write Tests
**Tasks:**
1. Create test_stt_service.py
   ```python
   TestSTTService
   - test_load_model()
   - test_transcribe_audio()
   - test_persian_text_handling()
   - test_error_handling()
   - test_batch_processing()
   ```

2. Integration tests
   - Upload → Transcribe → Create Activity
   - End-to-end workflow

**Deliverables:**
- ✅ 10+ STT tests
- ✅ Integration tests passing

#### Afternoon: Optimization & Polish
**Tasks:**
1. Performance optimization
   - Model quantization (if needed)
   - GPU support check
   - Parallel processing for batch

2. Error handling improvements
   - Invalid audio formats
   - Corrupted files
   - Long audio files

3. Documentation
   - Usage examples
   - API documentation

**Deliverables:**
- ✅ Optimized performance
- ✅ Robust error handling
- ✅ Documentation complete

**Phase 1 Complete:** ✅ Fully functional STT service

---

## 🎯 Phase 2: RAG System (Days 5-11)

**Goal:** Semantic search over CRM deals using ChromaDB + embeddings + Qwen2

### Day 5: ChromaDB Setup & Embedding Model

#### Morning: Environment Setup
**Tasks:**
1. Install dependencies
   ```bash
   pip install chromadb sentence-transformers
   pip install qwen-agent  # or transformers for Qwen2
   ```

2. Create vector store directory
   ```
   vector_store/
   ├── chroma_db/
   ├── embeddings_cache/
   └── config.json
   ```

3. Test ChromaDB
   - Create test collection
   - Add test documents
   - Query test vectors

**Deliverables:**
- ✅ ChromaDB installed and working
- ✅ Storage structure created
- ✅ Test collection functional

#### Afternoon: Embedding Model Integration
**Tasks:**
1. Load embedding model
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer(
       'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
   )
   ```

2. Create embedding service
   ```python
   services/embedding_service.py
   - load_model()
   - embed_text(text)
   - embed_batch(texts)
   ```

3. Test embeddings
   - Test Persian text
   - Test English text
   - Verify similarity scores

**Deliverables:**
- ✅ Embedding model loaded
- ✅ Embedding service created
- ✅ Embeddings tested

---

### Day 6: Document Ingestion & Indexing

#### Morning: Data Extraction
**Tasks:**
1. Extract CRM data for indexing
   ```python
   - Deal title + description
   - Activity notes
   - Combined deal context
   ```

2. Create document processor
   ```python
   services/document_processor.py
   - extract_deal_documents()
   - chunk_text(text, max_length=512)
   - prepare_for_indexing()
   ```

3. Add metadata
   - Deal ID
   - Timestamp
   - Deal status
   - Any custom fields

**Deliverables:**
- ✅ Data extraction working
- ✅ Document processor created
- ✅ Metadata attached

#### Afternoon: Index CRM Data
**Tasks:**
1. Create indexing pipeline
   ```python
   services/indexing_service.py
   - index_deals()
   - index_single_deal(deal_id)
   - update_index(deal_id)
   - delete_from_index(deal_id)
   ```

2. Implement batch indexing
   - Process all existing deals
   - Show progress
   - Handle errors

3. Test indexing
   - Index sample deals
   - Verify in ChromaDB
   - Check retrieval

**Deliverables:**
- ✅ Indexing pipeline functional
- ✅ All deals indexed
- ✅ ChromaDB populated

---

### Day 7: RAG Service Core

#### Full Day: RAG Service Implementation
**Tasks:**
1. Create RAG service structure
   ```python
   services/rag_service.py
   
   class RAGService:
       def __init__():
           - Load ChromaDB
           - Load embedding model
           - Initialize Qwen2
       
       def search(query, top_k=5):
           - Embed query
           - Search ChromaDB
           - Return results with metadata
       
       def ask(question):
           - Search relevant context
           - Build prompt
           - Query Qwen2
           - Return answer
       
       def index_new_deal(deal):
           - Extract text
           - Generate embedding
           - Store in ChromaDB
   ```

2. Implement semantic search
   - Query embedding
   - Similarity search
   - Re-ranking (optional)
   - Return top results

3. Context building
   - Select top K results
   - Format for LLM
   - Include metadata
   - Limit token count

**Deliverables:**
- ✅ RAGService class complete
- ✅ Semantic search working
- ✅ Context building functional

---

### Day 8: Qwen2 Integration

#### Morning: Qwen2 Setup
**Tasks:**
1. Install/Load Qwen2
   ```bash
   # Option 1: Via transformers
   pip install transformers>=4.37.0
   
   # Option 2: Via qwen-agent
   pip install qwen-agent
   ```

2. Load model
   ```python
   from transformers import AutoModelForCausalLM, AutoTokenizer
   
   model = AutoModelForCausalLM.from_pretrained(
       "Qwen/Qwen2-7B-Instruct",
       device_map="auto",
       torch_dtype="auto"
   )
   tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2-7B-Instruct")
   ```

3. Test generation
   - Simple prompt
   - Persian prompt
   - Context-based prompt

**Deliverables:**
- ✅ Qwen2 loaded
- ✅ Generation working
- ✅ Persian support verified

#### Afternoon: RAG + Qwen2 Pipeline
**Tasks:**
1. Implement question answering
   ```python
   def ask(question):
       # 1. Retrieve context
       results = self.search(question, top_k=3)
       context = self._format_context(results)
       
       # 2. Build prompt
       prompt = f"""
       بر اساس اطلاعات زیر به سوال پاسخ بده:
       
       اطلاعات:
       {context}
       
       سوال: {question}
       
       پاسخ:
       """
       
       # 3. Generate answer
       answer = self.qwen2_generate(prompt)
       return answer
   ```

2. Prompt engineering
   - System prompts
   - Few-shot examples
   - Persian-specific formatting

3. Test end-to-end
   - Ask test questions
   - Verify answers
   - Check accuracy

**Deliverables:**
- ✅ RAG + Qwen2 pipeline working
- ✅ Question answering functional
- ✅ Accuracy acceptable

---

### Day 9: Incremental Indexing & Cache

#### Morning: Real-time Indexing
**Tasks:**
1. Hook into deal creation
   - Auto-index new deals
   - Update on deal modification
   - Delete on deal deletion

2. Implement incremental updates
   ```python
   # In DealService or as observer
   def on_deal_created(deal):
       rag_service.index_new_deal(deal)
   
   def on_deal_updated(deal):
       rag_service.update_deal_index(deal)
   
   def on_deal_deleted(deal_id):
       rag_service.delete_from_index(deal_id)
   ```

3. Test real-time updates
   - Create deal → Check index
   - Update deal → Verify change
   - Delete deal → Confirm removal

**Deliverables:**
- ✅ Real-time indexing working
- ✅ Incremental updates functional
- ✅ Index stays synchronized

#### Afternoon: Caching & Optimization
**Tasks:**
1. Cache search results
   - Query hash → Results
   - TTL: 5-10 minutes
   - Using existing CacheService

2. Cache embeddings
   - Text hash → Embedding vector
   - Avoid re-embedding same text

3. Performance optimization
   - Batch embedding when possible
   - Limit vector dimensions if needed
   - Optimize ChromaDB queries

**Deliverables:**
- ✅ Search caching implemented
- ✅ Embedding cache working
- ✅ Performance improved

---

### Day 10: MCP Tools & Gradio UI

#### Morning: MCP Tools
**Tasks:**
1. Add RAG tools
   ```python
   mcp_spec/handlers/tool_handlers.py
   
   - search_deals_semantic(query, top_k)
   - ask_about_deals(question)
   - index_deal(deal_id)
   - search_with_filters(query, filters)
   ```

2. Add schemas
   ```python
   - SemanticSearchInput
   - AskQuestionInput
   - IndexDealInput
   ```

3. Test tools
   - Test each tool
   - Verify responses
   - Check error handling

**Deliverables:**
- ✅ 4 new RAG tools
- ✅ Schemas defined
- ✅ Tools tested

#### Afternoon: Gradio Interface
**Tasks:**
1. Add "RAG Search" tab
   - Query input box
   - Search button
   - Results display (deal cards)
   - Relevance scores

2. Add "Ask Questions" tab
   - Question input
   - Ask button
   - Answer display
   - Source deals shown

3. Implement callbacks
   - Handle searches
   - Display results
   - Format nicely

**Deliverables:**
- ✅ 2 new Gradio tabs
- ✅ Search UI functional
- ✅ Q&A UI working

---

### Day 11: Testing & Documentation

#### Morning: Write Tests
**Tasks:**
1. Create test_rag_service.py
   ```python
   TestRAGService
   - test_search_semantic()
   - test_ask_question()
   - test_indexing()
   - test_real_time_updates()
   - test_caching()
   ```

2. Integration tests
   - End-to-end RAG workflow
   - Index → Search → Answer

**Deliverables:**
- ✅ 10+ RAG tests
- ✅ Integration tests passing

#### Afternoon: Documentation & Polish
**Tasks:**
1. Document RAG system
   - Architecture
   - Usage examples
   - API documentation

2. Performance tuning
   - Optimize search speed
   - Tune vector parameters
   - Memory optimization

3. Error handling improvements
   - Handle edge cases
   - Better error messages

**Deliverables:**
- ✅ RAG documentation complete
- ✅ Performance optimized
- ✅ Robust error handling

**Phase 2 Complete:** ✅ Fully functional RAG system

---

## 🎯 Phase 3: Mixture of Experts (Days 12-21)

**Goal:** ML-based router + 4 expert models (Sentiment ✅, Summarization, NER, QA)

### Day 12: Architecture & Router Model Selection

#### Morning: MoE Architecture Design
**Tasks:**
1. Design MoE system
   ```
   User Query
       │
       ▼
   ┌─────────────┐
   │   Router    │ ← Small BERT classifier
   │   Model     │   (Task classification)
   └──────┬──────┘
          │
          ├──→ Expert 1: Sentiment ✅
          ├──→ Expert 2: Summarization
          ├──→ Expert 3: Entity Extraction
          └──→ Expert 4: Question Answering
   ```

2. Define task categories
   - Task 1: Sentiment Analysis
   - Task 2: Summarization
   - Task 3: Entity Extraction
   - Task 4: Question Answering
   - Task 5: General (fallback)

3. Create routing logic
   ```python
   services/moe_service.py (structure)
   
   class MoERouter:
       - load_router_model()
       - classify_task(query)
       - route(query, task_id)
   
   class ExpertManager:
       - register_expert(task_id, expert)
       - get_expert(task_id)
       - execute(task_id, query)
   ```

**Deliverables:**
- ✅ Architecture documented
- ✅ Task categories defined
- ✅ Service structure created

#### Afternoon: Router Model Selection
**Tasks:**
1. Choose router approach:
   
   **Option A: Rule-based (Quick Start)**
   - Keyword matching
   - Regex patterns
   - Fast, deterministic
   
   **Option B: ML-based (Better)**
   - Small BERT classifier
   - Trained on task classification
   - More accurate

2. For ML-based:
   - Find pre-trained model or
   - Prepare to fine-tune small BERT

3. Create training data (if needed)
   ```python
   task_examples = [
       ("این معامله چه احساسی داره؟", "sentiment"),
       ("این متن رو خلاصه کن", "summarization"),
       ("اسم مشتری چیه؟", "entity_extraction"),
       ("آخرین فعالیت چی بود؟", "question_answering"),
   ]
   ```

**Deliverables:**
- ✅ Router approach decided
- ✅ Training data prepared (if ML)
- ✅ Initial router implementation

---

### Day 13-14: Expert Models Setup

#### Day 13 Morning: Expert 2 - Summarization
**Tasks:**
1. Choose model
   ```python
   # Option 1: mT5 (multilingual)
   from transformers import MT5ForConditionalGeneration, MT5Tokenizer
   model = MT5ForConditionalGeneration.from_pretrained("google/mt5-base")
   
   # Option 2: Persian T5
   # Check Hugging Face for Persian T5 models
   ```

2. Create SummarizationExpert
   ```python
   services/experts/summarization_expert.py
   
   class SummarizationExpert:
       def __init__():
           - Load model
           - Load tokenizer
       
       def summarize(text, max_length=150):
           - Tokenize
           - Generate summary
           - Return text
   ```

3. Test summarization
   - Test with long deal descriptions
   - Verify Persian quality
   - Check speed

**Deliverables:**
- ✅ Summarization model loaded
- ✅ Expert class created
- ✅ Summarization tested

#### Day 13 Afternoon: Expert 3 - Entity Extraction (NER)
**Tasks:**
1. Choose NER model
   ```python
   # Option 1: Multilingual NER
   from transformers import AutoModelForTokenClassification, AutoTokenizer
   model = AutoModelForTokenClassification.from_pretrained(
       "Davlan/distilbert-base-multilingual-cased-ner-hrl"
   )
   
   # Option 2: Persian-specific NER
   # Check for Persian NER models on Hugging Face
   ```

2. Create EntityExtractionExpert
   ```python
   services/experts/entity_extraction_expert.py
   
   class EntityExtractionExpert:
       def __init__():
           - Load NER model
       
       def extract_entities(text):
           - Run NER
           - Return entities by type:
             {
               "persons": [...],
               "organizations": [...],
               "amounts": [...],
               "dates": [...]
             }
   ```

3. Test entity extraction
   - Test on deal descriptions
   - Verify entity types
   - Check accuracy

**Deliverables:**
- ✅ NER model loaded
- ✅ Expert class created
- ✅ Entity extraction tested

#### Day 14 Morning: Expert 4 - Question Answering
**Tasks:**
1. Choose QA model
   ```python
   # Option: XLM-RoBERTa for QA
   from transformers import AutoModelForQuestionAnswering, AutoTokenizer
   model = AutoModelForQuestionAnswering.from_pretrained(
       "deepset/xlm-roberta-large-squad2"
   )
   ```

2. Create QAExpert
   ```python
   services/experts/qa_expert.py
   
   class QAExpert:
       def __init__():
           - Load QA model
           - Initialize RAG service
       
       def answer_question(question, context=None):
           - If no context, use RAG
           - Run QA model
           - Return answer + confidence
   ```

3. Test QA
   - Test with deal questions
   - Verify Persian questions
   - Check with/without context

**Deliverables:**
- ✅ QA model loaded
- ✅ Expert class created
- ✅ QA tested

#### Day 14 Afternoon: Expert Integration
**Tasks:**
1. Register all experts
   ```python
   services/moe_service.py
   
   expert_manager = ExpertManager()
   expert_manager.register("sentiment", SentimentExpert())
   expert_manager.register("summarization", SummarizationExpert())
   expert_manager.register("entity_extraction", EntityExtractionExpert())
   expert_manager.register("question_answering", QAExpert())
   ```

2. Test expert manager
   - Call each expert
   - Verify responses
   - Check performance

**Deliverables:**
- ✅ All 4 experts registered
- ✅ Expert manager functional
- ✅ Individual experts tested

---

### Day 15-16: Router Training & Integration

#### Day 15: Router Model Training (if ML-based)
**Tasks:**
1. Prepare training dataset
   - 100-200 examples per task
   - Persian queries
   - Clear task labels

2. Fine-tune router model
   ```python
   # Use small BERT for efficiency
   from transformers import BertForSequenceClassification
   
   model = BertForSequenceClassification.from_pretrained(
       "bert-base-multilingual-cased",
       num_labels=5  # 5 tasks
   )
   
   # Fine-tune on task classification
   ```

3. Evaluate router
   - Test accuracy on validation set
   - Target: >90% accuracy
   - Check confusion matrix

**Deliverables:**
- ✅ Router model trained
- ✅ >90% classification accuracy
- ✅ Model saved

#### Day 16: MoE Service Integration
**Tasks:**
1. Complete MoEService
   ```python
   services/moe_service.py
   
   class MoEService:
       def __init__():
           - Load router
           - Load expert manager
       
       def process(query):
           # 1. Classify task
           task_id = self.router.classify(query)
           
           # 2. Route to expert
           expert = self.expert_manager.get_expert(task_id)
           
           # 3. Execute
           result = expert.execute(query)
           
           # 4. Format response
           return {
               "task": task_id,
               "expert": expert.name,
               "result": result,
               "confidence": confidence
           }
   ```

2. Add fallback logic
   - If low confidence, use multiple experts
   - Aggregate results
   - Return combined output

3. Test end-to-end
   - Various query types
   - Verify correct routing
   - Check results

**Deliverables:**
- ✅ MoEService complete
- ✅ Routing working correctly
- ✅ Fallback logic implemented

---

### Day 17: MCP Tools & Response Aggregation

#### Morning: MCP Tools
**Tasks:**
1. Add MoE tools
   ```python
   mcp_spec/handlers/tool_handlers.py
   
   - moe_analyze(query)  # Auto-route
   - summarize_text(text)  # Direct to summarization
   - extract_entities(text)  # Direct to NER
   - answer_question(question, context)  # Direct to QA
   ```

2. Add schemas
   ```python
   - MoEAnalyzeInput
   - SummarizeTextInput
   - ExtractEntitiesInput
   - AnswerQuestionInput
   ```

3. Test tools

**Deliverables:**
- ✅ 4 new MoE tools
- ✅ Tools tested
- ✅ Schemas defined

#### Afternoon: Multi-Expert Aggregation
**Tasks:**
1. Implement ensemble mode
   ```python
   def analyze_comprehensive(text):
       # Run multiple experts
       sentiment = sentiment_expert.analyze(text)
       summary = summarization_expert.summarize(text)
       entities = ner_expert.extract(text)
       
       return {
           "sentiment": sentiment,
           "summary": summary,
           "entities": entities
       }
   ```

2. Result formatting
   - Combine outputs nicely
   - Structured response
   - JSON format

3. Test aggregation
   - Multi-expert queries
   - Verify combined results

**Deliverables:**
- ✅ Multi-expert mode working
- ✅ Results aggregated properly
- ✅ Formatted responses

---

### Day 18: Gradio UI for MoE

#### Full Day: MoE Interface
**Tasks:**
1. Add "Multi-Expert Analysis" tab
   - Query input
   - Auto-detect task (show which expert)
   - Execute button
   - Results display

2. Add specific expert tabs:
   - "Summarization" tab
   - "Entity Extraction" tab
   - "Question Answering" tab

3. Implement UI components:
   - Expert selection dropdown (manual override)
   - Confidence display
   - Result highlighting
   - Export results button

4. Add visualizations:
   - Entity highlighting in text
   - Sentiment color coding
   - Summary comparison

**Deliverables:**
- ✅ 4 new Gradio tabs
- ✅ All UIs functional
- ✅ Visualizations working

---

### Day 19: Integration with Existing Services

#### Morning: Analytics Integration
**Tasks:**
1. Enhance AnalyticsService with MoE
   ```python
   services/analytics_service.py
   
   def analyze_deal_comprehensive(deal_id):
       # ... existing code ...
       
       # NEW: Add MoE analysis
       deal_text = deal.description
       
       moe_results = moe_service.analyze_comprehensive(deal_text)
       
       result["summary"] = moe_results["summary"]
       result["entities"] = moe_results["entities"]
       result["qa_capability"] = True
       
       return result
   ```

2. Use entities for insights
   - Extract key information
   - Populate deal fields
   - Generate better insights

3. Use summaries in reports
   - Executive summaries
   - Deal overviews

**Deliverables:**
- ✅ MoE integrated with Analytics
- ✅ Enhanced insights
- ✅ Better reports

#### Afternoon: RAG + MoE Integration
**Tasks:**
1. Combine RAG with QA expert
   ```python
   def ask_with_rag_and_qa(question):
       # 1. RAG retrieves context
       context = rag_service.search(question)
       
       # 2. QA expert answers with context
       answer = qa_expert.answer(question, context)
       
       return answer
   ```

2. Use summarization on RAG results
   - Summarize long contexts
   - Make answers concise

3. Test combined pipeline
   - RAG + QA
   - RAG + Summarization

**Deliverables:**
- ✅ RAG + MoE integrated
- ✅ Enhanced question answering
- ✅ Pipeline tested

---

### Day 20: Testing & Performance

#### Morning: Comprehensive Testing
**Tasks:**
1. Create test_moe_service.py
   ```python
   TestMoEService
   - test_router_classification()
   - test_each_expert()
   - test_routing_accuracy()
   - test_multi_expert_mode()
   - test_fallback_logic()
   ```

2. Create test_experts.py
   - TestSummarizationExpert
   - TestEntityExtractionExpert
   - TestQAExpert

3. Integration tests
   - End-to-end MoE workflows
   - RAG + MoE
   - Analytics + MoE

**Deliverables:**
- ✅ 20+ MoE tests
- ✅ All tests passing
- ✅ Integration verified

#### Afternoon: Performance Optimization
**Tasks:**
1. Model optimization
   - Quantization (int8)
   - Model pruning
   - Batch inference

2. Caching
   - Cache expert results
   - Cache router decisions
   - TTL strategies

3. Parallel execution
   - Run multiple experts in parallel
   - Async processing

4. Benchmark
   - Measure latency
   - Memory usage
   - Throughput

**Deliverables:**
- ✅ Optimized performance
- ✅ Caching implemented
- ✅ Benchmarks recorded

---

### Day 21: Documentation & Polish

#### Morning: Documentation
**Tasks:**
1. Write MoE documentation
   - Architecture overview
   - Each expert's purpose
   - Usage examples
   - API reference

2. Create tutorials
   - How to add new expert
   - How to retrain router
   - Troubleshooting guide

3. Update main README
   - New features section
   - Architecture diagrams
   - Quick start guide

**Deliverables:**
- ✅ Complete MoE documentation
- ✅ Tutorials written
- ✅ README updated

#### Afternoon: Final Polish
**Tasks:**
1. Code cleanup
   - Remove debug prints
   - Add docstrings
   - Format code

2. Error handling review
   - All edge cases covered
   - Clear error messages
   - Graceful degradation

3. Final testing
   - Run full test suite
   - Manual testing
   - Check all features

4. Deployment preparation
   - Update requirements.txt
   - Update Docker config
   - Create migration guide

**Deliverables:**
- ✅ Code polished
- ✅ All errors handled
- ✅ Ready for use

**Phase 3 Complete:** ✅ Fully functional MoE system

---

## 📊 Milestone Summary

### ✅ After Day 4: STT Complete
- Upload audio → Transcribe → Create activities
- MCP tools + Gradio UI
- Fully tested

### ✅ After Day 11: RAG Complete
- Semantic search over CRM data
- Question answering with Qwen2
- ChromaDB integrated
- MCP tools + Gradio UI
- Fully tested

### ✅ After Day 21: MoE Complete
- ML-based router working
- 4 experts operational (Sentiment, Summarization, NER, QA)
- Multi-expert aggregation
- Integrated with RAG + Analytics
- MCP tools + Gradio UI
- Fully tested

---

## 📋 Daily Checklist Template

For each day, use this checklist:

```
Day X: [Feature Name]

Morning Tasks:
□ Task 1
□ Task 2
□ Task 3

Afternoon Tasks:
□ Task 4
□ Task 5
□ Task 6

Testing:
□ Unit tests written
□ Integration tests passing
□ Manual testing completed

Documentation:
□ Code documented
□ API updated
□ README updated (if needed)

Deliverables:
□ Deliverable 1
□ Deliverable 2
□ Deliverable 3

Status: ⬜ Not Started | 🟡 In Progress | ✅ Complete
```

---

## 🎯 Success Criteria

### STT Success:
- ✅ Transcribe Persian audio with <10% WER
- ✅ Process within 2x real-time (1 min audio → 2 min processing)
- ✅ Auto-create activities from transcriptions
- ✅ 10+ tests passing

### RAG Success:
- ✅ Semantic search returns relevant deals >80% accuracy
- ✅ Q&A provides correct answers >75% of time
- ✅ Search latency <500ms
- ✅ Index stays synchronized with data
- ✅ 10+ tests passing

### MoE Success:
- ✅ Router classifies correctly >90% of time
- ✅ All 4 experts functional
- ✅ Latency <2 seconds end-to-end
- ✅ Multi-expert mode working
- ✅ 20+ tests passing

---

## 🚀 Getting Started

**Day 1 starts with:**
```bash
# 1. Create feature branch
git checkout -b feature/stt-service

# 2. Install dependencies
pip install openai-whisper soundfile librosa

# 3. Create service file
touch services/stt_service.py

# 4. Start coding!
```

---

## ❓ Decision Points

Throughout implementation, you'll need to decide:

### STT Decisions:
- Whisper model size (medium vs large)?
- CPU or GPU inference?
- Real-time vs batch processing?

### RAG Decisions:
- Qwen2 model size (1.5B, 7B, or 14B)?
- How many documents to retrieve (top_k)?
- Context window size for Qwen2?

### MoE Decisions:
- Rule-based or ML-based router?
- Train router from scratch or use pre-trained?
- Which specific models for each expert?

**Recommendation:** Start simple, then upgrade if needed!

---

**Ready to start? Begin with Day 1: STT Setup!** 🚀

**Questions or need guidance? Just ask!** 📝ss