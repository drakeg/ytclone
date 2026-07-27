variable "name" {
  description = "Name of the monthly AWS cost budget."
  type        = string
}

variable "monthly_limit_usd" {
  description = "Monthly budget limit in US dollars."
  type        = number
  default     = 15
}

variable "notification_emails" {
  description = "Email addresses that receive budget notifications."
  type        = list(string)

  validation {
    condition     = length(var.notification_emails) > 0
    error_message = "At least one budget notification email is required."
  }
}

variable "actual_alert_percent" {
  description = "Actual-spend percentage that triggers an alert."
  type        = number
  default     = 80
}

variable "forecast_alert_percent" {
  description = "Forecasted-spend percentage that triggers an alert."
  type        = number
  default     = 100
}

variable "project_tag_key" {
  description = "Cost allocation tag key used to scope the budget."
  type        = string
  default     = "Project"
}

variable "project_tag_value" {
  description = "Cost allocation tag value used to scope the budget."
  type        = string
}
