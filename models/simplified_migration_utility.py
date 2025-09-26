"""
Complete Updated Data Migration Utility for CSV to Model Conversion
Updated to match your snake_case database columns
"""

import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
import json

from models.deal_model import Deal, DealActivity, CRMAgent
from models.repositories import create_repositories

class DataMigrationUtility:
    """Utility class for migrating CSV data to the new model structure"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.repositories = create_repositories(db_manager)
        self.logger = logging.getLogger(__name__)
        
        # Define required columns from CSV (these will be filtered from larger CSV)
        self.required_deal_columns = {
            'Id': str,
            'Title': str,
            'Description': str,
            'RegisterTime': 'datetime',
            'Price': 'decimal',
            'Status': str,
            'PipelineStageId': str,
            'PipelineId': str,
            'ChangeToWonTime': 'datetime',
            'ChangeToLossTime': 'datetime',
            'LastTrackingTime': 'datetime',
            'NextTrackingTime': 'datetime',
            'LastActivityUpdateTime': 'datetime',
            'LastUpdateTime': 'datetime',
            'Probability': float,
            'ContactId': str,
            'LabelId': str,
            'LostReasonId': str,
            'LostReasonNote': str,
            'LostReasonOther': str,
            'IsIdle': bool,
            'IsRotten': bool,
            'IsRottenInStage': bool,
            'Fields': str,
            'Items': str,
            'MobilePhone': str
        }
        
        self.required_activity_columns = {
            'id': str,
            'title': str,
            'note': str,
            'resultnote': str,
            'activitytypeid': str,
            'isdone': bool,
            'duedate': 'datetime',
            'finishdate': 'datetime',
            'donedate': 'datetime',
            'registerdate': 'datetime',
            'lastupdatetime': 'datetime',
            'dealid': str,
            'creatorid': str,
            'ownerid': str,
            'updaterid': str
        }
        
        self.required_agent_columns = {
            'id': str,
            'groupowner': str,
            'ownername': str,
            'adminid': str,
            'role': str,
            'phone': str,
            'mobilephone': str,
            'personalid': str,
            'groupphone': str
        }
    
    def load_and_filter_csv(self, file_path: str, required_columns: Dict[str, Any], 
                           encoding: str = 'utf-8') -> pd.DataFrame:
        """Load CSV and filter to only required columns"""
        try:
            # Try different encodings
            encodings_to_try = [encoding, 'utf-8-sig', 'iso-8859-1', 'cp1252', 'latin1']
            
            df = None
            for enc in encodings_to_try:
                try:
                    df = pd.read_csv(file_path, encoding=enc)
                    self.logger.info(f"Successfully loaded {file_path} with encoding {enc}")
                    break
                except UnicodeDecodeError:
                    continue
                    
            if df is None:
                raise Exception(f"Could not decode file {file_path} with any encoding")
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            self.logger.info(f"Original CSV columns: {list(df.columns)}")
            
            # Filter to only required columns that exist in the CSV
            available_columns = set(df.columns)
            required_columns_set = set(required_columns.keys())
            
            columns_to_keep = list(available_columns.intersection(required_columns_set))
            
            # Log what we're keeping vs missing
            missing_columns = required_columns_set - available_columns
            extra_columns = available_columns - required_columns_set
            
            if missing_columns:
                self.logger.warning(f"Missing columns: {missing_columns}")
            if extra_columns:
                self.logger.info(f"Extra columns (will be ignored): {list(extra_columns)[:10]}...")
            
            self.logger.info(f"Keeping columns: {columns_to_keep}")
            
            # Keep only required columns
            if columns_to_keep:
                df_filtered = df[columns_to_keep].copy()
            else:
                df_filtered = pd.DataFrame()
            
            # Add missing columns with default values
            for col in missing_columns:
                if required_columns[col] == 'datetime':
                    df_filtered[col] = None
                elif required_columns[col] == 'decimal':
                    df_filtered[col] = None
                elif required_columns[col] == float:
                    df_filtered[col] = None
                elif required_columns[col] == bool:
                    df_filtered[col] = None
                else:  # string
                    df_filtered[col] = ""
            
            # Clean data
            df_filtered = df_filtered.replace('', None)
            df_filtered = df_filtered.where(pd.notna(df_filtered), None)
            
            self.logger.info(f"Filtered CSV shape: {df_filtered.shape}")
            return df_filtered
            
        except Exception as e:
            self.logger.error(f"Error loading and filtering CSV file {file_path}: {e}")
            return pd.DataFrame()
    
    def parse_datetime(self, date_str: Any) -> Optional[datetime]:
        """Parse datetime string with multiple format support"""
        if not date_str or pd.isna(date_str):
            return None
            
        if isinstance(date_str, datetime):
            return date_str
            
        try:
            formats = [
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y',
                '%m/%d/%Y %H:%M:%S',
                '%m/%d/%Y',
                '%Y/%m/%d %H:%M:%S',
                '%Y/%m/%d'
            ]
            
            date_str = str(date_str).strip()
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
                    
            result = pd.to_datetime(date_str, errors='coerce')
            return result if pd.notna(result) else None
            
        except Exception as e:
            self.logger.warning(f"Could not parse datetime: {date_str}, error: {e}")
            return None
    
    def parse_decimal(self, value: Any) -> Optional[Decimal]:
        """Parse decimal value"""
        if not value or pd.isna(value):
            return None
        try:
            return Decimal(str(value))
        except:
            return None
    
    def parse_boolean(self, value: Any) -> Optional[bool]:
        """Parse boolean value"""
        if value is None or pd.isna(value):
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'y', 't']
        if isinstance(value, (int, float)):
            return bool(value)
        return None
    
    def migrate_deals(self, csv_file_path: str) -> Dict[str, Any]:
        """Migrate deals from CSV to database"""
        try:
            self.logger.info("Starting deals migration...")
            
            df = self.load_and_filter_csv(csv_file_path, self.required_deal_columns)
            if df.empty:
                return {"success": False, "error": "Could not load or filter CSV file"}
            
            results = {
                "total_records": len(df),
                "successful_imports": 0,
                "failed_imports": 0,
                "errors": [],
                "skipped_records": 0
            }
            
            for index, row in df.iterrows():
                try:
                    if pd.isna(row.get('Id')) or not row.get('Id'):
                        results["skipped_records"] += 1
                        continue
                    
                    # Create Deal object with proper type conversion
                    deal_data = {}
                    
                    # String fields
                    string_fields = ['Id', 'Title', 'Description', 'Status', 'PipelineStageId', 
                                   'PipelineId', 'ContactId', 'LabelId', 'LostReasonId', 
                                   'LostReasonNote', 'LostReasonOther', 'Fields', 'Items', 'MobilePhone']
                    
                    for field in string_fields:
                        deal_data[field] = str(row.get(field, '')) if pd.notna(row.get(field)) else ''
                    
                    # Datetime fields
                    datetime_fields = ['RegisterTime', 'ChangeToWonTime', 'ChangeToLossTime',
                                     'LastTrackingTime', 'NextTrackingTime', 'LastActivityUpdateTime', 
                                     'LastUpdateTime']
                    
                    for field in datetime_fields:
                        deal_data[field] = self.parse_datetime(row.get(field))
                    
                    # Decimal fields
                    deal_data['Price'] = self.parse_decimal(row.get('Price'))
                    
                    # Float fields
                    prob_val = row.get('Probability')
                    deal_data['Probability'] = float(prob_val) if pd.notna(prob_val) else None
                    
                    # Boolean fields
                    boolean_fields = ['IsIdle', 'IsRotten', 'IsRottenInStage']
                    for field in boolean_fields:
                        deal_data[field] = self.parse_boolean(row.get(field))
                    
                    # Set missing fields with defaults
                    deal_data['OwnerId'] = ''  # Not in your database
                    deal_data['CreatorId'] = ''  # Not in your database
                    deal_data['Pin'] = False  # Not in your database
                    deal_data['Feedback'] = ''  # Not in your database
                    deal_data['ExpectedCloseDate'] = None  # Not in your database
                    
                    # Create Deal object
                    deal = Deal.from_dict(deal_data)
                    
                    # Save to database
                    deal_id = self.repositories.deals.create_deal(deal)
                    
                    if deal_id:
                        results["successful_imports"] += 1
                        if results["successful_imports"] % 100 == 0:
                            self.logger.info(f"Processed {results['successful_imports']} deals...")
                    else:
                        results["failed_imports"] += 1
                        results["errors"].append(f"Row {index}: Failed to create deal - {deal.Title}")
                        
                except Exception as e:
                    results["failed_imports"] += 1
                    error_msg = f"Row {index}: {str(e)}"
                    results["errors"].append(error_msg)
                    if len(results["errors"]) <= 10:
                        self.logger.error(error_msg)
            
            results["success"] = True
            self.logger.info(f"Deals migration completed: {results['successful_imports']} successful, "
                           f"{results['failed_imports']} failed, {results['skipped_records']} skipped")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in deals migration: {e}")
            return {"success": False, "error": str(e)}
    
    def migrate_activities(self, csv_file_path: str) -> Dict[str, Any]:
        """Migrate activities from CSV to database"""
        try:
            self.logger.info("Starting activities migration...")
            
            df = self.load_and_filter_csv(csv_file_path, self.required_activity_columns)
            if df.empty:
                return {"success": False, "error": "Could not load or filter CSV file"}
            
            results = {
                "total_records": len(df),
                "successful_imports": 0,
                "failed_imports": 0,
                "errors": [],
                "skipped_records": 0
            }
            
            for index, row in df.iterrows():
                try:
                    if pd.isna(row.get('id')) or not row.get('id') or pd.isna(row.get('dealid')):
                        results["skipped_records"] += 1
                        continue
                    
                    # Create Activity object with proper type conversion
                    activity_data = {}
                    
                    # String fields
                    string_fields = ['id', 'title', 'note', 'resultnote', 'activitytypeid',
                                   'dealid', 'creatorid', 'ownerid', 'updaterid']
                    
                    for field in string_fields:
                        activity_data[field] = str(row.get(field, '')) if pd.notna(row.get(field)) else ''
                    
                    # Datetime fields
                    datetime_fields = ['duedate', 'finishdate', 'donedate', 'registerdate', 'lastupdatetime']
                    
                    for field in datetime_fields:
                        activity_data[field] = self.parse_datetime(row.get(field))
                    
                    # Boolean fields
                    boolean_fields = ['isdone']
                    for field in boolean_fields:
                        activity_data[field] = self.parse_boolean(row.get(field))
                    
                    # Set missing fields with defaults
                    activity_data['isprivate'] = False  # Not in your database
                    activity_data['ispinned'] = False  # Not in your database
                    
                    # Create DealActivity object
                    activity = DealActivity.from_dict(activity_data)
                    
                    # Save to database
                    activity_id = self.repositories.activities.create_activity(activity)
                    
                    if activity_id:
                        results["successful_imports"] += 1
                        if results["successful_imports"] % 100 == 0:
                            self.logger.info(f"Processed {results['successful_imports']} activities...")
                    else:
                        results["failed_imports"] += 1
                        results["errors"].append(f"Row {index}: Failed to create activity - {activity.title}")
                        
                except Exception as e:
                    results["failed_imports"] += 1
                    error_msg = f"Row {index}: {str(e)}"
                    results["errors"].append(error_msg)
                    if len(results["errors"]) <= 10:
                        self.logger.error(error_msg)
            
            results["success"] = True
            self.logger.info(f"Activities migration completed: {results['successful_imports']} successful, "
                           f"{results['failed_imports']} failed, {results['skipped_records']} skipped")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in activities migration: {e}")
            return {"success": False, "error": str(e)}
    
    def migrate_agents(self, csv_file_path: str) -> Dict[str, Any]:
        """Migrate CRM agents from CSV to database"""
        try:
            self.logger.info("Starting agents migration...")
            
            df = self.load_and_filter_csv(csv_file_path, self.required_agent_columns)
            if df.empty:
                return {"success": False, "error": "Could not load or filter CSV file"}
            
            results = {
                "total_records": len(df),
                "successful_imports": 0,
                "failed_imports": 0,
                "errors": [],
                "skipped_records": 0
            }
            
            for index, row in df.iterrows():
                try:
                    if pd.isna(row.get('id')) or not row.get('id'):
                        results["skipped_records"] += 1
                        continue
                    
                    # Create Agent object with proper type conversion
                    agent_data = {}
                    
                    # All agent fields are strings
                    for field in self.required_agent_columns.keys():
                        agent_data[field] = str(row.get(field, '')) if pd.notna(row.get(field)) else ''
                    
                    # Create CRMAgent object
                    agent = CRMAgent.from_dict(agent_data)
                    
                    # Save to database
                    agent_id = self.repositories.agents.create_agent(agent)
                    
                    if agent_id:
                        results["successful_imports"] += 1
                        if results["successful_imports"] % 50 == 0:
                            self.logger.info(f"Processed {results['successful_imports']} agents...")
                    else:
                        results["failed_imports"] += 1
                        results["errors"].append(f"Row {index}: Failed to create agent - {agent.ownername}")
                        
                except Exception as e:
                    results["failed_imports"] += 1
                    error_msg = f"Row {index}: {str(e)}"
                    results["errors"].append(error_msg)
                    if len(results["errors"]) <= 10:
                        self.logger.error(error_msg)
            
            results["success"] = True
            self.logger.info(f"Agents migration completed: {results['successful_imports']} successful, "
                           f"{results['failed_imports']} failed, {results['skipped_records']} skipped")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in agents migration: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """Validate data integrity after migration"""
        try:
            self.logger.info("Starting data integrity validation...")
            
            validation_results = {
                "deals": {},
                "activities": {},
                "agents": {},
                "relationships": {},
                "data_quality": {}
            }
            
            # Validate deals
            deals = self.repositories.deals.get_all_deals()
            validation_results["deals"] = {
                "total_count": len(deals),
                "with_prices": len([d for d in deals if d.Price]),
                "won_deals": len([d for d in deals if d.ChangeToWonTime]),
                "lost_deals": len([d for d in deals if d.ChangeToLossTime]),
                "active_deals": len([d for d in deals if not d.ChangeToWonTime and not d.ChangeToLossTime]),
                "rotten_count": len([d for d in deals if d.IsRotten or d.IsRottenInStage]),
            }
            
            # Validate activities
            all_activities = []
            for deal in deals:
                activities = self.repositories.activities.get_activities_by_deal(deal.Id)
                all_activities.extend(activities)
            
            validation_results["activities"] = {
                "total_count": len(all_activities),
                "done_count": len([a for a in all_activities if a.isdone]),
                "with_due_dates": len([a for a in all_activities if a.duedate]),
                "with_owners": len([a for a in all_activities if a.ownerid]),
            }
            
            # Validate agents
            agents = self.repositories.agents.get_all_agents()
            validation_results["agents"] = {
                "total_count": len(agents),
                "with_roles": len([a for a in agents if a.role]),
                "with_phones": len([a for a in agents if a.mobilephone or a.phone]),
            }
            
            # Validate relationships
            orphaned_activities = len([a for a in all_activities 
                                     if a.dealid and not any(d.Id == a.dealid for d in deals)])
            
            validation_results["relationships"] = {
                "orphaned_activities": orphaned_activities,
                "deals_with_activities": len([d for d in deals if any(a.dealid == d.Id for a in all_activities)]),
            }
            
            # Data quality checks
            deals_with_missing_titles = len([d for d in deals if not d.Title or d.Title.strip() == ''])
            activities_with_missing_notes = len([a for a in all_activities if not a.note and not a.resultnote])
            
            validation_results["data_quality"] = {
                "deals_with_missing_titles": deals_with_missing_titles,
                "activities_with_missing_notes": activities_with_missing_notes,
                "deals_with_future_register_dates": len([d for d in deals if d.RegisterTime and d.RegisterTime > datetime.now()]),
            }
            
            self.logger.info("Data integrity validation completed")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error in data integrity validation: {e}")
            return {"error": str(e)}
    
    def generate_migration_report(self, deals_result: Dict, activities_result: Dict, 
                                 agents_result: Dict, validation_result: Dict = None) -> str:
        """Generate a comprehensive migration report"""
        
        report = []
        report.append("=" * 70)
        report.append("DATA MIGRATION REPORT")
        report.append("=" * 70)
        report.append(f"Migration completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Deals migration
        report.append("DEALS MIGRATION:")
        report.append(f"  Total records processed: {deals_result.get('total_records', 0)}")
        report.append(f"  Successful imports: {deals_result.get('successful_imports', 0)}")
        report.append(f"  Failed imports: {deals_result.get('failed_imports', 0)}")
        report.append(f"  Skipped records: {deals_result.get('skipped_records', 0)}")
        if deals_result.get('errors'):
            report.append(f"  Sample errors: {deals_result['errors'][:3]}")
        report.append("")
        
        # Activities migration
        report.append("ACTIVITIES MIGRATION:")
        report.append(f"  Total records processed: {activities_result.get('total_records', 0)}")
        report.append(f"  Successful imports: {activities_result.get('successful_imports', 0)}")
        report.append(f"  Failed imports: {activities_result.get('failed_imports', 0)}")
        report.append(f"  Skipped records: {activities_result.get('skipped_records', 0)}")
        if activities_result.get('errors'):
            report.append(f"  Sample errors: {activities_result['errors'][:3]}")
        report.append("")
        
        # Agents migration
        report.append("AGENTS MIGRATION:")
        report.append(f"  Total records processed: {agents_result.get('total_records', 0)}")
        report.append(f"  Successful imports: {agents_result.get('successful_imports', 0)}")
        report.append(f"  Failed imports: {agents_result.get('failed_imports', 0)}")
        report.append(f"  Skipped records: {agents_result.get('skipped_records', 0)}")
        if agents_result.get('errors'):
            report.append(f"  Sample errors: {agents_result['errors'][:3]}")
        report.append("")
        
        # Success rates
        deals_rate = (deals_result.get('successful_imports', 0) / max(deals_result.get('total_records', 1), 1)) * 100
        activities_rate = (activities_result.get('successful_imports', 0) / max(activities_result.get('total_records', 1), 1)) * 100
        agents_rate = (agents_result.get('successful_imports', 0) / max(agents_result.get('total_records', 1), 1)) * 100
        
        report.append("SUCCESS RATES:")
        report.append(f"  Deals: {deals_rate:.1f}%")
        report.append(f"  Activities: {activities_rate:.1f}%")
        report.append(f"  Agents: {agents_rate:.1f}%")
        report.append("")
        
        # Validation results
        if validation_result and 'deals' in validation_result:
            report.append("DATA VALIDATION:")
            deals_val = validation_result['deals']
            activities_val = validation_result['activities']
            agents_val = validation_result['agents']
            
            report.append(f"  Total deals in database: {deals_val.get('total_count', 0)}")
            report.append(f"    - Active: {deals_val.get('active_deals', 0)}")
            report.append(f"    - Won: {deals_val.get('won_deals', 0)}")
            report.append(f"    - Lost: {deals_val.get('lost_deals', 0)}")
            report.append(f"    - With prices: {deals_val.get('with_prices', 0)}")
            report.append("")
            report.append(f"  Total activities in database: {activities_val.get('total_count', 0)}")
            report.append(f"    - Completed: {activities_val.get('done_count', 0)}")
            report.append(f"    - With owners: {activities_val.get('with_owners', 0)}")
            report.append("")
            report.append(f"  Total agents in database: {agents_val.get('total_count', 0)}")
            report.append("")
            
            # Data quality issues
            quality = validation_result.get('data_quality', {})
            if quality:
                report.append("DATA QUALITY ISSUES:")
                for issue, count in quality.items():
                    if count > 0:
                        report.append(f"  - {issue.replace('_', ' ').title()}: {count}")
                report.append("")
        
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def run_full_migration(self, deals_csv: str, activities_csv: str, agents_csv: str) -> Dict[str, Any]:
        """Run full migration process"""
        try:
            self.logger.info("Starting full data migration process...")
            
            # Step 1: Migrate agents first
            agents_result = self.migrate_agents(agents_csv)
            
            # Step 2: Migrate deals
            deals_result = self.migrate_deals(deals_csv)
            
            # Step 3: Migrate activities
            activities_result = self.migrate_activities(activities_csv)
            
            # Step 4: Validate data integrity
            validation_result = self.validate_data_integrity()
            
            # Step 5: Generate report
            report = self.generate_migration_report(deals_result, activities_result, agents_result, validation_result)
            
            total_successful = (deals_result.get('successful_imports', 0) + 
                              activities_result.get('successful_imports', 0) + 
                              agents_result.get('successful_imports', 0))
            
            total_records = (deals_result.get('total_records', 1) + 
                           activities_result.get('total_records', 1) + 
                           agents_result.get('total_records', 1))
            
            full_result = {
                "success": True,
                "deals": deals_result,
                "activities": activities_result,
                "agents": agents_result,
                "validation": validation_result,
                "report": report,
                "summary": {
                    "total_deals_imported": deals_result.get('successful_imports', 0),
                    "total_activities_imported": activities_result.get('successful_imports', 0),
                    "total_agents_imported": agents_result.get('successful_imports', 0),
                    "overall_success_rate": (total_successful / max(total_records, 1)) * 100
                }
            }
            
            self.logger.info("Full data migration process completed")
            print(report)
            
            return full_result
            
        except Exception as e:
            error_msg = f"Error in full migration process: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}


# Example usage script
def main():
    """Example usage of the migration utility"""
    import logging
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Example usage:
    # from database.database import DatabaseManager
    # db_manager = DatabaseManager()
    # migrator = DataMigrationUtility(db_manager)
    # 
    # result = migrator.run_full_migration(
    #     deals_csv="Deals.csv",
    #     activities_csv="activities.csv", 
    #     agents_csv="crmteam.csv"
    # )
    
    pass


if __name__ == "__main__":
    main()