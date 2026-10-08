from service.work_order_logic import decide_follow_up


def test_return_visit_is_visible_in_dispatch_decision() -> None:
    matches = [
        {
            "score": 0.98,
            "metadata": {
                "text": "Temporary cooling restored. Ordered replacement capacitor. Technician will return Wednesday 8am-10am."
            },
        },
        {
            "score": 0.84,
            "metadata": {
                "text": "Customer approved follow-up visit once part arrives."
            },
        },
    ]

    result = decide_follow_up(
        question="Did the technician schedule a return visit?",
        matches=matches,
        work_order_id="WO-1007",
    )

    assert result.follow_up_status == "return_visit_required"
    assert result.recommended_action == "Keep the dispatch open and confirm the return appointment with the customer."
    assert "temporary fix" in result.answer.lower()
