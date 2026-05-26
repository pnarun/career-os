/** Client-side fallback suggestions (works offline; merged with API results). */

export const ROLE_SUGGESTIONS = [
  "Angular Developer",
  "Senior Angular Developer",
  "React Developer",
  "Senior React Developer",
  "Full Stack Developer",
  "Senior Full Stack Developer",
  "Node.js Developer",
  "Python Developer",
  "Java Developer",
  "Backend Developer",
  "Frontend Developer",
  "DevOps Engineer",
  "Cloud Engineer",
  "Software Engineer",
  "Senior Software Engineer",
]

export const SKILL_SUGGESTIONS = [
  "Angular",
  "AngularJS",
  "React",
  "TypeScript",
  "JavaScript",
  "Node.js",
  "Python",
  "Java",
  "Spring Boot",
  "MongoDB",
  "PostgreSQL",
  "AWS",
  "Docker",
  "Kubernetes",
  "REST API",
  "GraphQL",
  "Machine Learning",
]

export const LOCATION_SUGGESTIONS = [
  "Remote",
  "Hybrid",
  "India",
  "Bangalore",
  "Bengaluru",
  "Hyderabad",
  "Chennai",
  "Pune",
  "Mumbai",
  "Delhi NCR",
  "Gurgaon",
  "Noida",
  "Kolkata",
  "Ahmedabad",
  "Kochi",
  "Jaipur",
  "Indore",
  "Chandigarh",
]

export const COMPANY_SUGGESTIONS = [
  "Amazon",
  "Flipkart",
  "Google",
  "Microsoft",
  "Infosys",
  "TCS",
  "Wipro",
  "Accenture",
  "PhonePe",
  "Razorpay",
  "Swiggy",
  "Zomato",
  "Freshworks",
  "Adobe",
  "Uber",
  "Myntra",
]

export function filterLocalSuggestions(pool, query, items, limit = 12) {
  const q = (query || "").trim().toLowerCase()
  const selected = new Set(items.map((i) => i.toLowerCase()))
  let list = pool.filter((s) => !selected.has(s.toLowerCase()))
  if (q) {
    list = list.filter((s) => s.toLowerCase().includes(q))
  }
  return list.slice(0, limit)
}
