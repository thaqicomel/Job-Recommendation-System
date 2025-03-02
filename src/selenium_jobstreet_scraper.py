import time
import random
import pandas as pd
import csv
from datetime import datetime
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

class JobStreetScraper:
    def __init__(self, location="Malaysia", num_pages=5, headless=False):
        """
        Initialize the JobStreet Malaysia scraper.
        
        Args:
            location (str): The location to search for jobs (default: Malaysia)
            num_pages (int): Number of pages to scrape per query
            headless (bool): Whether to run Chrome in headless mode
        """
        self.base_url = "https://www.jobstreet.com.my"
        self.location = location
        self.num_pages = num_pages
        self.jobs = []
        
        # User agents to rotate
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        
        # Initialize the driver
        self.driver = self._setup_driver(headless)
    
    def _setup_driver(self, headless):
        """Set up the Chrome WebDriver with appropriate options."""
        options = Options()
        if headless:
            options.add_argument("--headless")
        
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Install and setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Set the user agent
        driver.execute_cdp_cmd("Network.setUserAgentOverride", {
            "userAgent": random.choice(self.user_agents)
        })
        
        # Add necessary cookies
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })
        
        return driver
    
    def __del__(self):
        """Close the driver when the object is deleted."""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except:
            pass
    
    def _human_like_delay(self, min_seconds=2, max_seconds=5):
        """Add a random delay to simulate human behavior."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def _human_like_scroll(self):
        """Scroll the page like a human would."""
        total_height = int(self.driver.execute_script("return document.body.scrollHeight"))
        viewport_height = int(self.driver.execute_script("return window.innerHeight"))
        
        for i in range(0, total_height, viewport_height // 3):
            self.driver.execute_script(f"window.scrollTo(0, {i});")
            self._human_like_delay(0.1, 0.3)
        
        # Scroll back up randomly
        if random.random() < 0.3:
            self.driver.execute_script("window.scrollTo(0, 0);")
            self._human_like_delay(0.5, 1)
    
    def _build_search_url(self, query="", page=1):
        """Build the URL for JobStreet search."""
        # For JobStreet Malaysia
        if query:
            return f"{self.base_url}/jobs?q={query}&l={self.location}&page={page}"
        else:
            return f"{self.base_url}/jobs/in-{self.location.lower()}?page={page}"
    
    def _accept_cookies_if_present(self):
        """Accept cookies dialog if it appears."""
        try:
            # Multiple possible selectors for the cookie button
            cookie_buttons = [
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'I agree')]",
                "//button[contains(text(), 'Accept all')]",
                "//button[contains(@id, 'cookie')]",
                "//button[contains(@class, 'cookie')]"
            ]
            
            for button_xpath in cookie_buttons:
                try:
                    cookie_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, button_xpath))
                    )
                    cookie_button.click()
                    self._human_like_delay(1, 2)
                    return True
                except (TimeoutException, NoSuchElementException):
                    continue
            
            return False
        except Exception as e:
            print(f"Error handling cookies: {e}")
            return False
    
    def _close_popups(self):
        """Close any popups that might appear."""
        try:
            # Look for common popup close buttons
            close_buttons = [
                "//button[contains(@aria-label, 'Close')]",
                "//button[contains(@class, 'close')]",
                "//div[contains(@class, 'close')]",
                "//span[contains(@class, 'close')]",
                "//button[contains(text(), 'No thanks')]"
            ]
            
            for button_xpath in close_buttons:
                try:
                    close_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, button_xpath))
                    )
                    close_button.click()
                    self._human_like_delay(1, 2)
                    return True
                except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
                    continue
            
            return False
        except Exception as e:
            print(f"Error handling popups: {e}")
            return False
    
    def _extract_job_data(self, job_card):
        """Extract job information from a job card element."""
        try:
            # JobStreet has different HTML structure than Indeed
            
            # Extract job title
            try:
                title_element = job_card.find_element(By.CSS_SELECTOR, "h1.sx2jih0, .job-title, [data-automation='job-title']")
                job_title = title_element.text.strip()
            except NoSuchElementException:
                try:
                    title_element = job_card.find_element(By.CSS_SELECTOR, "a h1, a[data-automation='jobTitle']")
                    job_title = title_element.text.strip()
                except NoSuchElementException:
                    job_title = "N/A"
            
            # Extract job URL
            try:
                job_link = job_card.find_element(By.TAG_NAME, "a")
                job_url = job_link.get_attribute("href")
                # Extract job ID from URL if possible
                job_id_match = re.search(r'/(\d+)(?:\?|$)', job_url)
                job_id = job_id_match.group(1) if job_id_match else f"job_{random.randint(10000, 99999)}"
            except (NoSuchElementException, AttributeError):
                job_url = "N/A"
                job_id = f"job_{random.randint(10000, 99999)}"
            
            # Extract company name
            try:
                company_element = job_card.find_element(By.CSS_SELECTOR, ".sx2jih0 span, [data-automation='jobCompany'], .company-name")
                company = company_element.text.strip()
            except NoSuchElementException:
                company = "N/A"
            
            # Extract job location
            try:
                location_element = job_card.find_element(By.CSS_SELECTOR, "[data-automation='jobLocation'], .location")
                location = location_element.text.strip()
            except NoSuchElementException:
                location = "N/A"
            
            # Extract job description snippet
            try:
                description_element = job_card.find_element(By.CSS_SELECTOR, ".job-description, [data-automation='jobShortDescription'], .sx2jih0 > div:nth-child(2)")
                description = description_element.text.strip()
            except NoSuchElementException:
                description = "N/A"
            
            # Extract salary if available
            try:
                salary_element = job_card.find_element(By.CSS_SELECTOR, "[data-automation='jobSalary'], .salary")
                salary = salary_element.text.strip()
            except NoSuchElementException:
                salary = "N/A"
            
            # Extract job type if available
            try:
                job_type_element = job_card.find_element(By.CSS_SELECTOR, "[data-automation='jobType'], .job-type")
                job_type = job_type_element.text.strip()
            except NoSuchElementException:
                job_type = "N/A"
            
            # Extract posting date
            try:
                date_element = job_card.find_element(By.CSS_SELECTOR, "[data-automation='jobListingDate'], .listing-date, .sx2jih0 > span:last-child")
                posting_date = date_element.text.strip()
            except NoSuchElementException:
                posting_date = "N/A"
            
            # Try to extract industry/category
            industry = "Not specified"
            # JobStreet often has category info
            try:
                industry_element = job_card.find_element(By.CSS_SELECTOR, "[data-automation='jobIndustry'], .job-category")
                industry = industry_element.text.strip()
            except NoSuchElementException:
                # If no specific element, try to extract from title or description
                for category in ["Finance", "IT", "Healthcare", "Education", "Manufacturing", "Sales", "Marketing", "Engineering", "Admin", "Hospitality"]:
                    if category.lower() in job_title.lower() or category.lower() in description.lower():
                        industry = category
                        break
            
            # Try to extract skills from description
            skills = []
            common_skills = ["python", "java", "sql", "excel", "communication", "leadership", "teamwork", "project management", "analysis", "problem solving"]
            for skill in common_skills:
                if skill.lower() in description.lower():
                    skills.append(skill)
            
            return {
                'job_id': job_id,
                'job_title': job_title,
                'company': company,
                'location': location,
                'description': description,
                'salary': salary,
                'job_type': job_type,
                'posting_date': posting_date,
                'job_url': job_url,
                'industry': industry,
                'skills': ", ".join(skills) if skills else "Not specified",
                'scraped_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"Error extracting job data: {e}")
            return None
    
    def scrape_job_details(self, job_url):
        """Visit the job page and scrape detailed information."""
        try:
            # Open the job page in a new tab
            self.driver.execute_script(f"window.open('{job_url}', '_blank');")
            self._human_like_delay(1, 2)
            
            # Switch to the new tab
            self.driver.switch_to.window(self.driver.window_handles[1])
            self._human_like_delay(3, 5)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job-description, [data-automation='jobDetailsDescription']"))
            )
            
            # Scroll like a human
            self._human_like_scroll()
            
            # Extract full job description
            try:
                job_description_element = self.driver.find_element(By.CSS_SELECTOR, ".job-description, [data-automation='jobDetailsDescription']")
                full_description = job_description_element.text.strip()
            except NoSuchElementException:
                full_description = "Failed to retrieve full description"
            
            # Extract additional details specific to JobStreet
            job_details = {}
            
            # Career level / Experience level
            try:
                career_level_element = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Career Level')]/following-sibling::*")
                job_details['experience_level'] = career_level_element.text.strip()
            except NoSuchElementException:
                job_details['experience_level'] = "Not specified"
            
            # Qualification
            try:
                qualification_element = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Qualification')]/following-sibling::*")
                job_details['qualification'] = qualification_element.text.strip()
            except NoSuchElementException:
                job_details['qualification'] = "Not specified"
            
            # Years of experience
            try:
                years_exp_element = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Years of Experience')]/following-sibling::*")
                job_details['years_of_experience'] = years_exp_element.text.strip()
            except NoSuchElementException:
                job_details['years_of_experience'] = "Not specified"
            
            # Required skills
            try:
                skills_elements = self.driver.find_elements(By.CSS_SELECTOR, ".skill-tag, [data-automation='skills'] span")
                skills = [element.text.strip() for element in skills_elements]
                job_details['required_skills'] = ", ".join(skills)
            except NoSuchElementException:
                job_details['required_skills'] = "Not specified"
            
            # Close the tab and switch back
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return {'full_description': full_description, **job_details}
            
        except Exception as e:
            print(f"Error scraping job details: {e}")
            
            # Make sure to close the tab and switch back if an error occurs
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
                
            return {'full_description': "Failed to retrieve full description"}
    
    def scrape_jobs(self, job_queries=None):
        """
        Scrape jobs from JobStreet based on queries.
        
        Args:
            job_queries (list): List of job query strings to search for
        """
        if job_queries is None:
            job_queries = ["data scientist", "data analyst", "project manager", "business analyst"]
        
        total_jobs_scraped = 0
        
        try:
            for query in job_queries:
                print(f"Searching for: {query} in {self.location}")
                
                for page in range(1, self.num_pages + 1):  # JobStreet uses 1-based page indexing
                    url = self._build_search_url(query, page)
                    print(f"Scraping page {page}/{self.num_pages}: {url}")
                    
                    try:
                        # Load the page
                        self.driver.get(url)
                        self._human_like_delay(3, 6)
                        
                        # Accept cookies if the dialog appears
                        self._accept_cookies_if_present()
                        
                        # Close any popups
                        self._close_popups()
                        
                        # Scroll to load all content
                        self._human_like_scroll()
                        
                        # Wait for job cards to load
                        try:
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "article, [data-automation='jobListing'], .sx2jih0"))
                            )
                        except TimeoutException:
                            print(f"No job cards found on page {page} or page took too long to load")
                            continue
                        
                        # Find all job cards
                        job_cards = self.driver.find_elements(By.CSS_SELECTOR, "article, [data-automation='jobListing'], .sx2jih0")
                        
                        if not job_cards:
                            print(f"No job cards found on page {page}")
                            break
                        
                        print(f"Found {len(job_cards)} job cards on page {page}")
                        
                        # Process each job card
                        for job_card in job_cards:
                            job_data = self._extract_job_data(job_card)
                            
                            if job_data:
                                job_data['search_query'] = query
                                
                                # Option to get detailed job description (uncomment if needed)
                                # if job_data['job_url'] != "N/A" and random.random() < 0.3:  # Only get details for ~30% of jobs
                                #     details = self.scrape_job_details(job_data['job_url'])
                                #     job_data.update(details)
                                
                                self.jobs.append(job_data)
                                total_jobs_scraped += 1
                                
                                # Print progress
                                if total_jobs_scraped % 10 == 0:
                                    print(f"Scraped {total_jobs_scraped} jobs so far")
                        
                        # Random delay before the next page
                        self._human_like_delay(5, 10)
                        
                    except Exception as e:
                        print(f"Error scraping page {page}: {e}")
                        continue
                
                # Extra delay between different queries
                self._human_like_delay(8, 15)
                
                # Switch user agent occasionally
                if random.random() < 0.5:
                    self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {
                        "userAgent": random.choice(self.user_agents)
                    })
        
        finally:
            # Always close the driver when done
            self.driver.quit()
        
        print(f"Total jobs scraped: {total_jobs_scraped}")
        return self.jobs
    
    def save_to_csv(self, filename="jobstreet_malaysia_jobs.csv"):
        """Save scraped job data to a CSV file."""
        if not self.jobs:
            print("No jobs to save.")
            return
        
        try:
            # Add timestamp to filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_with_timestamp = f"{os.path.splitext(filename)[0]}_{timestamp}{os.path.splitext(filename)[1]}"
            
            df = pd.DataFrame(self.jobs)
            df.to_csv(filename_with_timestamp, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
            print(f"Successfully saved {len(self.jobs)} jobs to {filename_with_timestamp}")
            return filename_with_timestamp
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            return None

def main():
    # Job search queries to use (add or remove as needed)
    job_queries = [
        "data scientist", 
        "data analyst", 
        "software engineer", 
        "business analyst",
        "machine learning",
        "data engineer"
    ]
    
    # Initialize the scraper
    scraper = JobStreetScraper(
        location="Malaysia",
        num_pages=5,  # Adjust based on your needs
        headless=False  # Set to True for headless mode
    )
    
    # Scrape jobs
    jobs = scraper.scrape_jobs(job_queries)
    
    # Save to CSV
    scraper.save_to_csv("jobstreet_malaysia_jobs2.csv")

if __name__ == "__main__":
    main()