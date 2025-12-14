"""Test Phase 1 - Core infrastructure"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("\n1️⃣ Testing imports...")
    try:
        from config.settings import MODEL_CHOICES, CHUNK_SIZE, QDRANT_COLLECTION_NAME
        print("   ✓ config.settings imported")
    except Exception as e:
        print(f"   ✗ config.settings failed: {e}")
        return False
    
    try:
        from config.prompts import get_system_prompt
        print("   ✓ config.prompts imported")
    except Exception as e:
        print(f"   ✗ config.prompts failed: {e}")
        return False
    
    try:
        from llm.factory import get_llm, get_openai_eval_llm
        print("   ✓ llm.factory imported")
    except Exception as e:
        print(f"   ✗ llm.factory failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration values"""
    print("\n2️⃣ Testing configuration...")
    try:
        from config.settings import MODEL_CHOICES, CHUNK_SIZE, EMBEDDING_MODEL_NAME
        
        assert CHUNK_SIZE == 1000, "CHUNK_SIZE incorrect"
        print(f"   ✓ CHUNK_SIZE = {CHUNK_SIZE}")
        
        assert "openai" in MODEL_CHOICES, "openai not in MODEL_CHOICES"
        print(f"   ✓ MODEL_CHOICES has {len(MODEL_CHOICES)} providers")
        
        assert EMBEDDING_MODEL_NAME == "all-MiniLM-L6-v2"
        print(f"   ✓ EMBEDDING_MODEL_NAME = {EMBEDDING_MODEL_NAME}")
        
        return True
    except AssertionError as e:
        print(f"   ✗ Config test failed: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

def test_prompts():
    """Test prompt generation"""
    print("\n3️⃣ Testing prompts...")
    try:
        from config.prompts import get_system_prompt
        
        # Single document
        prompt = get_system_prompt(["doc_1"], prompt_style="Standard")
        assert "expert Oracle DBA" in prompt, "Expert DBA not in prompt"
        assert "doc_1" in prompt, "Doc ID not in prompt"
        print("   ✓ Single document - Standard style")
        
        # Multiple documents
        prompt = get_system_prompt(["doc_1", "doc_2"], "Detailed Step-by-Step")
        assert "STEP" in prompt, "Steps not in prompt"
        assert "doc_1" in prompt and "doc_2" in prompt, "Doc IDs not in prompt"
        print("   ✓ Multi-document - Detailed style")
        
        # Issue-focused
        prompt = get_system_prompt(["doc_1"], "Issue-Focused")
        assert "EXECUTIVE SUMMARY" in prompt, "Summary not in prompt"
        print("   ✓ Single document - Issue-Focused style")
        
        return True
    except AssertionError as e:
        print(f"   ✗ Prompt test failed: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

def test_embeddings():
    """Test embedding manager"""
    print("\n4️⃣ Testing embeddings...")
    try:
        from core.embeddings import get_embedding_manager
        
        print("   ⏳ Initializing embedding manager (this may take a moment)...")
        manager = get_embedding_manager()
        
        vector_size = manager.get_vector_size()
        assert vector_size == 384, f"Expected vector_size 384, got {vector_size}"
        print(f"   ✓ Vector size = {vector_size}")
        
        embeddings = manager.get_embeddings()
        assert embeddings is not None, "Embeddings is None"
        print("   ✓ Embeddings initialized")
        
        # Test singleton
        manager2 = get_embedding_manager()
        assert manager is manager2, "Singleton pattern failed"
        print("   ✓ Singleton pattern working")
        
        return True
    except AssertionError as e:
        print(f"   ✗ Embeddings test failed: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vector_store():
    """Test vector store manager"""
    print("\n5️⃣ Testing vector store...")
    try:
        from core.vector_store import VectorStoreManager
        
        print("   ⏳ Initializing vector store...")
        vs = VectorStoreManager()
        print("   ✓ VectorStoreManager initialized")
        
        stats = vs.get_collection_stats()
        assert "points_count" in stats, "points_count not in stats"
        print(f"   ✓ Collection stats: {stats['points_count']} points")
        
        vectorstore = vs.get_vectorstore()
        assert vectorstore is not None, "vectorstore is None"
        print("   ✓ Vectorstore object created")
        
        return True
    except AssertionError as e:
        print(f"   ✗ Vector store test failed: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_retriever():
    """Test retriever"""
    print("\n6️⃣ Testing retriever...")
    try:
        from core.vector_store import VectorStoreManager
        from core.retriever import DocumentRetriever
        
        vs = VectorStoreManager()
        retriever = DocumentRetriever(vs)
        print("   ✓ DocumentRetriever initialized")
        
        assert retriever.vectorstore_manager is not None
        print("   ✓ Retriever has vectorstore manager")
        
        # Test unfiltered retriever creation
        unfiltered = retriever.get_unfiltered_retriever(k=5)
        assert unfiltered is not None
        print("   ✓ Unfiltered retriever created")
        
        # Test filtered retriever creation
        filtered = retriever.get_filtered_retriever(["doc_1"], k=5)
        assert filtered is not None
        print("   ✓ Filtered retriever created")
        
        return True
    except AssertionError as e:
        print(f"   ✗ Retriever test failed: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_factory():
    """Test LLM factory"""
    print("\n7️⃣ Testing LLM factory...")
    try:
        from llm.factory import get_llm, get_openai_eval_llm
        
        print("   ✓ LLM factory functions imported")
        
        # Test that functions exist and are callable
        assert callable(get_llm), "get_llm is not callable"
        assert callable(get_openai_eval_llm), "get_openai_eval_llm is not callable"
        print("   ✓ Factory functions are callable")
        
        # Test error handling (no API key)
        try:
            get_llm("openai", "", "gpt-4o")
            print("   ✗ Should have raised ValueError for missing API key")
            return False
        except ValueError as e:
            print("   ✓ Correctly raises ValueError for missing API key")
        
        # Test invalid provider
        try:
            get_llm("invalid", "key", "model")
            print("   ✗ Should have raised ValueError for invalid provider")
            return False
        except ValueError as e:
            print("   ✓ Correctly raises ValueError for invalid provider")
        
        return True
    except AssertionError as e:
        print(f"   ✗ LLM factory test failed: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("🧪 PHASE 1 - CORE INFRASTRUCTURE TESTS")
    print("="*60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    if not results[0][1]:
        print("\n❌ Cannot continue - imports failed")
        return False
    
    results.append(("Configuration", test_config()))
    results.append(("Prompts", test_prompts()))
    results.append(("Embeddings", test_embeddings()))
    results.append(("Vector Store", test_vector_store()))
    results.append(("Retriever", test_retriever()))
    results.append(("LLM Factory", test_llm_factory()))
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("="*60)
    print(f"Result: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - PHASE 1 COMPLETE!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - see details above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)