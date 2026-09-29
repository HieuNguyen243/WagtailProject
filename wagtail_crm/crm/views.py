from django.contrib.auth.decorators import permission_required
from django.shortcuts import render

from crm.ai_analysis import AIAnalysisError, build_crm_report, request_ai_analysis


@permission_required("crm.view_order")
def ai_report(request):
	report = build_crm_report()
	analysis = None
	error = None
	prompt = request.POST.get("prompt", "").strip()

	if request.method == "POST":
		if len(prompt) > 500:
			error = "Câu lệnh không được dài quá 500 ký tự."
		else:
			try:
				analysis = request_ai_analysis(report, prompt)
			except AIAnalysisError as exc:
				error = str(exc)

	return render(
		request,
		"crm/ai_report.html",
		{
			"report": report,
			"analysis": analysis,
			"error": error,
			"prompt": prompt,
		},
	)
