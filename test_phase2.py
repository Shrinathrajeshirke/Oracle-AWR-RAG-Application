"""Test Phase 2 - Ingestor & Evaluation"""
import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_document_processor():
    """Test document processor"""
    print("\n✓ Testing DocumentProcessor...")
    from ingestor.processor import DocumentProcessor
    
    processor = DocumentProcessor()
    assert processor is not None
    print("  ✓ DocumentProcessor initialized")
    return True

def test_metadata_manager():
    """Test metadata manager"""
    print("\n✓ Testing MetadataManager...")
    from ingestor.metadata_manager import MetadataManager
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        metadata_file = f.name
    
    try:
        mgr = MetadataManager(metadata_file)
        assert mgr is not None
        print("  ✓ MetadataManager initialized")
        
        # Register document
        mgr.register_document("doc_1", "test.pdf", 10, 1024)
        assert mgr.document_exists("doc_1")
        print("  ✓ Document registered")
        
        # Get info
        info = mgr.get_document_info("doc_1")
        assert info['filename'] == "test.pdf"
        print("  ✓ Document info retrieved")
        
        # Get stats
        stats = mgr.get_statistics()
        assert stats['total_documents'] == 1
        print("  ✓ Statistics retrieved")
        
        # Update status
        mgr.update_document_status("doc_1", "indexed")
        print("  ✓ Status updated")
        
        return True
    finally:
        os.unlink(metadata_file)

def test_ragas_evaluator():
    """Test RAGAS evaluator"""
    print("\n✓ Testing RAGASEvaluator...")
    from evaluation.ragas_evaluator import RAGASEvaluator
    
    evaluator = RAGASEvaluator()
    assert evaluator is not None
    print("  ✓ RAGASEvaluator initialized")
    
    # Get empty summary
    summary = evaluator.get_evaluation_summary()
    assert summary['message'] == "No evaluations run yet"
    print("  ✓ Empty summary retrieved")
    
    return True

def test_custom_metrics():
    """Test custom metrics"""
    print("\n✓ Testing CustomMetrics...")
    from evaluation.metrics import CustomMetrics
    
    answer = "We recommend implementing indexes. CPU is at 85%. Priority: High"
    contexts = ["Index performance", "CPU usage metrics"]
    
    # Test individual metrics
    completeness = CustomMetrics.metric_completeness(answer)
    assert 0 <= completeness <= 1
    print(f"  ✓ Completeness: {completeness:.2%}")
    
    actionability = CustomMetrics.metric_actionability(answer)
    assert 0 <= actionability <= 1
    print(f"  ✓ Actionability: {actionability:.2%}")
    
    specificity = CustomMetrics.metric_specificity(answer, contexts)
    assert 0 <= specificity <= 1
    print(f"  ✓ Specificity: {specificity:.2%}")
    
    structure = CustomMetrics.metric_structure(answer)
    assert 0 <= structure <= 1
    print(f"  ✓ Structure: {structure:.2%}")
    
    relevance = CustomMetrics.metric_relevance_to_context(answer, contexts)
    assert 0 <= relevance <= 1
    print(f"  ✓ Relevance: {relevance:.2%}")
    
    # Test overall
    overall = CustomMetrics.compute_overall_quality_score(answer, contexts)
    assert "overall_quality" in overall
    print(f"  ✓ Overall Quality: {overall['overall_quality']:.2%}")
    
    return True

def main():
    print("="*60)
    print("🧪 PHASE 2 - INGESTOR & EVALUATION TESTS")
    print("="*60)
    
    results = []
    
    results.append(("DocumentProcessor", test_document_processor()))
    results.append(("MetadataManager", test_metadata_manager()))
    results.append(("RAGASEvaluator", test_ragas_evaluator()))
    results.append(("CustomMetrics", test_custom_metrics()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 PHASE 2 TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL PHASE 2 TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)