from datetime import datetime
import os

def init_models(db):
    """Initialize all models with the database instance"""
    
    class ContentItem(db.Model):
        """Model for storing liberation intelligence content items"""
        __tablename__ = 'content_items'
        
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(255), nullable=False)
        content = db.Column(db.Text, nullable=False)
        content_type = db.Column(db.String(50), nullable=False)  # daily_analysis, resistance_stories, etc.
        category = db.Column(db.String(100), nullable=False)
        file_path = db.Column(db.String(500), nullable=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        published_date = db.Column(db.Date, nullable=True)
        content_metadata = db.Column(db.JSON, nullable=True)
        is_active = db.Column(db.Boolean, default=True)
        
        def __repr__(self):
            return f'<ContentItem {self.title}>'
        
        def to_dict(self):
            """Convert content item to dictionary for API responses"""
            return {
                'id': self.id,
                'title': self.title,
                'content': self.content,
                'content_type': self.content_type,
                'category': self.category,
                'file_path': self.file_path,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'published_date': self.published_date.isoformat() if self.published_date else None,
                'metadata': self.content_metadata,
                'is_active': self.is_active
            }

    class PowerMapping(db.Model):
        """Model for storing power mapping analysis"""
        __tablename__ = 'power_mappings'
        
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(255), nullable=False)
        description = db.Column(db.Text, nullable=True)
        target_organization = db.Column(db.String(255), nullable=True)
        power_level = db.Column(db.String(50), nullable=True)  # high, medium, low
        influence_type = db.Column(db.String(100), nullable=True)  # economic, political, social
        geographic_scope = db.Column(db.String(100), nullable=True)
        key_relationships = db.Column(db.JSON, nullable=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        is_active = db.Column(db.Boolean, default=True)
        
        def __repr__(self):
            return f'<PowerMapping {self.title}>'

    class OrganizingAction(db.Model):
        """Model for tracking organizing actions and campaigns"""
        __tablename__ = 'organizing_actions'
        
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(255), nullable=False)
        description = db.Column(db.Text, nullable=True)
        action_type = db.Column(db.String(100), nullable=False)  # protest, boycott, petition, etc.
        location = db.Column(db.String(255), nullable=True)
        date_planned = db.Column(db.DateTime, nullable=True)
        organizers = db.Column(db.JSON, nullable=True)
        target_outcome = db.Column(db.Text, nullable=True)
        status = db.Column(db.String(50), default='planned')  # planned, active, completed, cancelled
        impact_assessment = db.Column(db.Text, nullable=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f'<OrganizingAction {self.title}>'

    class SystemicIssue(db.Model):
        """Model for tracking systemic racism issues and analysis"""
        __tablename__ = 'systemic_issues'
        
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(255), nullable=False)
        description = db.Column(db.Text, nullable=False)
        issue_category = db.Column(db.String(100), nullable=False)  # housing, education, healthcare, etc.
        geographic_scope = db.Column(db.String(100), nullable=True)
        affected_communities = db.Column(db.JSON, nullable=True)
        root_causes = db.Column(db.JSON, nullable=True)
        policy_connections = db.Column(db.JSON, nullable=True)
        severity_level = db.Column(db.String(50), nullable=True)  # critical, high, medium, low
        analysis_data = db.Column(db.JSON, nullable=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f'<SystemicIssue {self.title}>'

    class ResistanceStory(db.Model):
        """Model for documenting community resistance and victories"""
        __tablename__ = 'resistance_stories'
        
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(255), nullable=False)
        story_content = db.Column(db.Text, nullable=False)
        community_involved = db.Column(db.String(255), nullable=True)
        location = db.Column(db.String(255), nullable=True)
        date_occurred = db.Column(db.Date, nullable=True)
        victory_type = db.Column(db.String(100), nullable=True)  # policy_change, direct_action, etc.
        impact_description = db.Column(db.Text, nullable=True)
        lessons_learned = db.Column(db.Text, nullable=True)
        supporting_documents = db.Column(db.JSON, nullable=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f'<ResistanceStory {self.title}>'

    class DataSource(db.Model):
        """Model for tracking data sources and their reliability"""
        __tablename__ = 'data_sources'
        
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255), nullable=False)
        url = db.Column(db.String(500), nullable=True)
        source_type = db.Column(db.String(100), nullable=False)  # government, academic, community, etc.
        reliability_score = db.Column(db.Float, nullable=True)  # 0-1 scale
        bias_assessment = db.Column(db.Text, nullable=True)
        last_verified = db.Column(db.DateTime, nullable=True)
        access_method = db.Column(db.String(100), nullable=True)  # api, scraping, manual, etc.
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f'<DataSource {self.name}>'

    # Return all models in a dictionary
    return {
        'ContentItem': ContentItem,
        'PowerMapping': PowerMapping,
        'OrganizingAction': OrganizingAction,
        'SystemicIssue': SystemicIssue,
        'ResistanceStory': ResistanceStory,
        'DataSource': DataSource
    }
