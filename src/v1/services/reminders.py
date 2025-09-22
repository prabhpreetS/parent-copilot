from src.v1.services.model import get_response
from src.v1.utils.prompts import (SYSTEM_PROMPT_EVENT_EXTRACTOR,
                                  USER_PROMPT_EVENT_EXTRACTOR,
                                  system_p)
from src.v1.services.memory_engine.retrieval_memory import get_supabase_client
import re
from datetime import datetime
import json
import logging
import sys
import asyncio

# Configure logging at the top of the file
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TODAYS_DATE = datetime.now().strftime("%d-%m-%Y")

def clean_nulls(d):
    return {k: (None if v == "null" else v) for k, v in d.items()}

async def reminder(text, user_id, document_id, system_prompt = system_p):
    try:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]

        for chunk in chunks:
            inserted = False
            print('chunk:::::::>>>>>>>>',chunk[:100])
            user_prompt_event_extractor = USER_PROMPT_EVENT_EXTRACTOR.format(
                contract=chunk,
                TODAYS_DATE=TODAYS_DATE
            )
            token, response, model = await get_response(
                user_prompt_event_extractor,
                system_prompt,
                response_format="json_object",
                temperature=0.5,
                model='anthropic'
            )

            # Ensure response is JSON
            if isinstance(response, str):
                try:
                    response = json.loads(response)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON string from model for user {user_id}")
                    return {"error": "Invalid JSON response from model"}

            # If it's a single dictionary, wrap it in a list for consistent processing
            if isinstance(response, dict):
                response = [response]

            # Now process list of dicts
            for extracted_json in response:
                if isinstance(extracted_json, dict):
                    extracted_json['user_id'] = user_id
                    extracted_json['document_id'] = document_id

                    # Initialize Supabase Client
                    supabase = get_supabase_client()
                    insert_data = clean_nulls({
                        'frequency': extracted_json['frequency'],
                        'day_of_week': extracted_json['day_of_week'],
                        'time': extracted_json.get('time'),
                        'week_pattern': extracted_json.get('week_pattern'),
                        'specific_date': extracted_json.get('specific_date'),
                        'notification_text': extracted_json.get('notification_text'),
                        'user_id': extracted_json['user_id'],
                        'document_id': extracted_json['document_id'],
                        'day_of_month': extracted_json.get('day_of_month'),
                        'month': extracted_json.get('month'),
                        'event_type': extracted_json.get('event_type'),
                    })
                    # Normalize 'time' field if it's in HH:MM:SS+00:00 format
                    time_value = insert_data.get("time")
                    if isinstance(time_value, str) and re.match(r"^\d{2}:\d{2}:\d{2}\+00:00$", time_value):
                        current_year = datetime.utcnow().year
                        normalized_time = f"{current_year}-01-01T{time_value}"
                        logger.warning(f"Normalizing 'time' field from '{time_value}' to '{normalized_time}' for user {user_id}")
                        insert_data["time"] = normalized_time
                    logger.debug(f"Cleaned insert data for user {user_id}: {insert_data}")

                    # Insert into Supabase
                    supabase_response = supabase.table("ai_reminders").insert([insert_data]).execute()
                    inserted = True
                    logger.info(f"Inserted reminder into Supabase for user_id: {user_id}. Response: {supabase_response.data}")
                else:
                    logger.warning(f"Unexpected item in response list: {extracted_json}")
            if not inserted:
                logger.warning(f"No reminders were inserted for user_id: {user_id} in this chunk.")
                return {"error": "No valid reminders were found or inserted."}
 
        if isinstance(response, (dict, list)):
            if inserted:
                logger.info(f"Successfully processed reminders for user_id: {user_id}, document_id: {document_id}")
            else:
                logger.warning(f"No reminders were inserted for user_id: {user_id}")
        else:
            try:
                response = json.loads(response)
                logger.info(f"Response successfully parsed as JSON for user {user_id}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed for user {user_id}: {str(e)}")
                logger.debug(f"Raw response: {response}")
                return {"error": "Invalid JSON response from model"}

        return response

    except Exception as e:
        logger.exception(f"Unexpected error occurred while processing reminder for user {user_id}: {str(e)}")
        return {"error": "An unexpected error occurred. Please try again later."}
              

###################################
async def process_chunk(chunk, user_id, document_id, system_prompt):
    """Process a single chunk independently"""
    try:
        print('chunk:::::::>>>>>>>>',chunk[:100])
        user_prompt_event_extractor = USER_PROMPT_EVENT_EXTRACTOR.format(
            contract=chunk,
            TODAYS_DATE=TODAYS_DATE
        )
        token, response, model = await get_response(
            user_prompt_event_extractor,
            system_prompt,
            response_format="json_object",
            temperature=0.5,
            model='anthropic'
        )

        # Ensure response is JSON
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON string from model for user {user_id}")
                return {"error": "Invalid JSON response from model"}

        # If it's a single dictionary, wrap it in a list for consistent processing
        if isinstance(response, dict):
            response = [response]

        inserted_count = 0
        # Process list of dicts
        for extracted_json in response:
            if isinstance(extracted_json, dict):
                extracted_json['user_id'] = user_id
                extracted_json['document_id'] = document_id

                # Initialize Supabase Client
                supabase = get_supabase_client()
                insert_data = clean_nulls({
                    'frequency': extracted_json['frequency'],
                    'day_of_week': extracted_json['day_of_week'],
                    'time': extracted_json.get('time'),
                    'week_pattern': extracted_json.get('week_pattern'),
                    'specific_date': extracted_json.get('specific_date'),
                    'notification_text': extracted_json.get('notification_text'),
                    'user_id': extracted_json['user_id'],
                    'document_id': extracted_json['document_id'],
                    'day_of_month': extracted_json.get('day_of_month'),
                    'month': extracted_json.get('month'),
                    'event_type': extracted_json.get('event_type'),
                })
                
                # Normalize 'time' field if it's in HH:MM:SS+00:00 format
                time_value = insert_data.get("time")
                if isinstance(time_value, str) and re.match(r"^\d{2}:\d{2}:\d{2}\+00:00$", time_value):
                    current_year = datetime.utcnow().year
                    normalized_time = f"{current_year}-01-01T{time_value}"
                    logger.warning(f"Normalizing 'time' field from '{time_value}' to '{normalized_time}' for user {user_id}")
                    insert_data["time"] = normalized_time
                
                logger.debug(f"Cleaned insert data for user {user_id}: {insert_data}")

                # Insert into Supabase
                supabase_response = supabase.table("ai_reminders").insert([insert_data]).execute()
                inserted_count += 1
                logger.info(f"Inserted reminder into Supabase for user_id: {user_id}. Response: {supabase_response.data}")
            else:
                logger.warning(f"Unexpected item in response list: {extracted_json}")
        
        return {"success": True, "inserted_count": inserted_count, "chunk_data": response}
    
    except Exception as e:
        logger.exception(f"Error processing chunk for user {user_id}: {str(e)}")
        return {"error": f"Chunk processing failed: {str(e)}"}

async def reminder1(text, user_id, document_id, system_prompt=system_p):
    """Main function with parallel processing"""
    try:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        
        # Process all chunks in parallel
        tasks = [
            process_chunk(chunk, user_id, document_id, system_prompt) 
            for chunk in chunks
        ]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        total_inserted = 0
        all_responses = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_msg = f"Chunk {i} failed with exception: {str(result)}"
                logger.error(error_msg)
                errors.append(error_msg)
            elif isinstance(result, dict):
                if "error" in result:
                    errors.append(f"Chunk {i}: {result['error']}")
                else:
                    total_inserted += result.get("inserted_count", 0)
                    if "chunk_data" in result:
                        all_responses.extend(result["chunk_data"] if isinstance(result["chunk_data"], list) else [result["chunk_data"]])
        
        if errors:
            logger.warning(f"Some chunks failed for user {user_id}: {errors}")
        
        if total_inserted == 0:
            logger.warning(f"No reminders were inserted for user_id: {user_id}")
            return {"error": "No valid reminders were found or inserted.", "chunk_errors": errors}
        
        logger.info(f"Successfully processed {total_inserted} reminders for user_id: {user_id}, document_id: {document_id}")
        return {
            "success": True,
            "total_inserted": total_inserted,
            "responses": all_responses,
            "errors": errors if errors else None
        }
        
    except Exception as e:
        logger.exception(f"Unexpected error occurred while processing reminder for user {user_id}: {str(e)}")
        return {"error": "An unexpected error occurred. Please try again later."}
###################################
   

if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Test the reminder function
        test_text = """DOCKET NO. AAN FA23 5023838 S	:				SUPERIOR COURT

TINA YOUNG	:				JUDICIAL DISTRICT OF

V.	:				ANSONIA-MILFORD

ANDREW YOUNG	:				APRIL 18, 2024


PARENTING PLAN
ARTICLE I: CUSTODY
1.1 	The parties shall share joint legal custody of their minor children, Mali Rose Young DOB 7/6/12 and Mya Sky Young, DOB 9/19/16. 
1.2   The Father and Mother agree that they will confer with reference to matters of policy involving the children, as to topics such as health and medical care, religion, education, camps and activities, and the parties agree that they will attempt to adopt a harmonious policy best suited to the interests of the children.  Except as may be otherwise set forth herein, routine "day to day" decisions shall be made by each parent during the times that the children are with him or her.
1.3   All major decisions affecting the children shall be made by the parties jointly, with each parent to have an equal voice in such decisions.  In addition, the parties shall confer whenever differences arise or decisions are to be made or changes brought about affecting the children's lives with respect to such non-routine matters such as his education, financial matters, religious training, illness and operations, and other matters of similar importance.  Each party shall have an equal voice in making a decision on such matters.
1.4     The parties shall exert reasonable effort to maintain free access and unhampered contact between the children and each of the parties and to foster a feeling of affection between the children and the parties.  Neither party shall make any comment that tends to denigrate the other parent to or in the presence or hearing of the children.  Neither party shall do anything that may estrange the children from the other party, nor injure the opinions of the children as to the other parent, nor act in such a way as to hamper the free and natural development of the children's love and respect for the other parent.  
1.5   Each of the parties agrees to keep the other informed as to the whereabouts of the children, including their address and phone number, while the child is with the Father or Mother.  Each party will, similarly notify the other of the location, phone number and names of supervisory adults where the children will be staying in the event the children are not going to be with a parent. 
1.6   If either party has knowledge of any illness or accident or other circumstances seriously affecting the health or welfare of the children, that party will promptly notify the other.  Each party will, similarly, notify the other of any other change in the children's medical status, including visits to any doctor or dentist or prescription medications.
1.7   In the event or illness or personal injury to the children, the first party to learn of such illness or injury shall notify the other immediately and each party shall keep the other informed at all times of the whereabouts of the children.  For the purposes of this paragraph, the word "illness" shall mean any sickness or ailment that requires the services of a physician.  The word "injury" shall mean any injury that requires the services of a physician.
1.8	The parents shall not involve the minor children in adult conversations or disputes, and shall not use the minor children as messengers to convey information, ask questions, or adjust the schedule. 






ARTICLE II: PARENTING SCHEDULE
2.1	The parties shall share parenting time with the minor children as follows:






2.2	In the event either parent needs to request a change in the parenting schedule, he/she shall provide at least 24 hours notice. If the other parent cannot accommodate a change in schedule, it will be the parent's responsibility whose time it is to make alternative arrangements.
2.4	The party about to begin their parenting time shall be responsible for picking the minor children up from the other parent (or from school, activities, or the like), unless mutually agreed in writing otherwise.
2.5	Both parents shall be entitled to attend the children's sports, activities, school events and the like regardless of which parent is exercising time.
ARTICLE III: HOLIDAY/VACATION SCHEDULE
3.1   Holidays shall be allocated between the parties as they may agree, or if they cannot agree the parties shall alternate the following holidays, as follows:
Easter: Mother shall have parenting time on Easter in odd years, Father shall have parenting time on Easter in even years.
MLK, Indigenous people's day, Memorial Day and labor day- Each parent shall have two of these holidays, ideally to be aligned with the weekend, and then returning the children to school on Tuesday.
Thanksgiving – Father shall have parenting time in odd years, Mother shall have parenting time in even years. Parenting time shall be defined as Wednesday, Thursday and Friday with the option for the full weekend. If this creates 3 weekends in a row for one parent, the parties agree that they will adjust the schedule so that it becomes 2 weekends with one parent, 2 weekends with the other parent, ultimately then resetting the schedule. 
Christmas Eve/Christmas Day – Father shall have parenting time annually on Christmas Eve to being either on 12/23 or on 12/24 at 10:30 a.m., to be determined each year. In odd years Father's Christmas Eve parenting time shall extend until 12/25 at 12 p.m. In even years Father's Christmas Eve parenting time shall extend until 12/24 at 9/9:30 .m. Mother shall have parenting time annually on Christmas Day. In odd years Mother's Christmas parenting time shall be from 12/25 at 12 p.m. until 12/26 at 10:30 a.m. In even years Mother's Christmas parenting time shall be from 12/24 at 9/9:30 p.m. until 12/26 at 10:30 a.m.

3.2	The parties shall have reasonable access to the children while the children are with the other party, including phone calls, Facetime visits, and email during reasonable hours of the day and evening.  
3.3	The child shall spend his or her birthday with the parent who has the children on the relevant day, in accordance with the parenting plan. On a child's birthday, allowance will be made for the parent with whom a child is not residing on that day to visit or telephone and exchange good wishes and/or gifts.
3.4	 Each parent may take up to two (2) weeks of vacation with the minor children.  The parents shall provide written notice to the other parent of their respective summer plans at least thirty (30) days in advance. Both parties shall provide the other the following information for any vacation:  (i) the duration of the trip; (ii) the name and address of each place where the minor child or children will spend each night; (iii) landline telephone numbers, if applicable; (iv) airline name(s), flight numbers, and times of departure if applicable; and, (v) similar information concerning other means of travel such as rail or boat. In the event of conflict, Mother's weeks shall take precedence in even years, Father's weeks shall take precedence in odd years. 
3.4	Winter Break - The winter break period shall be 12/26 until 12/30 at 10.30am with one parent, and 12/30 at 10.30am until return to school on 1/2 with the other parent. In odd years, Father shall spend the first half of the break with the children and the Mother shall spend the second  half of the break with the children. In even years, the Mother shall spend the first half of the break with the children and the Father shall spend the second half of the break with the children. If Father is looking to travel over the Christmas break, the parents agree to support him having the first half of the break to do so and having the children available for an early morning departure on the 26th.

Spring Break - The parties will continue to split spring break, continuing the tradition of both being in Florida during that time. If Father wishes to have a full week with the children instead of splitting the spring break, then he may utilize the February/president weekend break and take the children out of school for a few days around that weekend to allow such. If they will be sharing spring break, February break would be alternated. 

Summer Break – The parties shall each be entitled to two weeks of vacation parenting time with the minor children. They shall exchange weeks by May 1st and May 5th annually. The Wife shall have first choice in even years, the Husband shall have the first choice in odd years. 

3.5	The Holiday and Vacation schedule shall supersede the regular weekly schedule.  If a holiday is not referenced above, the regular schedule shall remain in effect unless the Mother and Father agree otherwise.
3.6	The parties intend the foregoing parenting plan to provide a flexible framework that may be adjusted, upon mutual agreement, to meet specific needs and circumstances. A need for flexibility and adjustment is specifically anticipated as follows: (a) Allowances will be made for early pick-up and drop-off times for vacations, holidays and special events, (b) The parenting plan will be flexible to allow for the children's attendance at family functions, such as birthdays, weddings, etc.  Each party shall give the other as much advance notice as reasonably possible as to the date, time and nature of all such special events, (c) Nothing contained herein shall preclude the parties from making adjustment and changes in the parenting plan, to allow for such things as the schedules of the parties and/or the children or for vacations or other events, provided such changes are discussed by both parties in advance and made by mutual agreement.
IV. POST-SECONDARY EDUCATION


Signed, Sealed and Delivered
In the presence of:


_____________________________  		_______________________________
						
Plaintiff						Defendant					



_____________________________			_______________________________
			
Attorney for the Plaintiff			Attorney for the Defendant
"""
        test_user_id = "test_user_123"
        test_document_id = "test_document_123"
        result = await reminder(test_text, test_user_id, test_document_id)
        print("Result::::::::::::::::>>>>>>><<<<<<>>>>>>>>>>>", result)
    
    # Run the async main function
    asyncio.run(main())