output "budget_name" {
  description = "Name of the AWS monthly cost budget."
  value       = aws_budgets_budget.monthly.name
}
