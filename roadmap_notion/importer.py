#!/usr/bin/env python3
"""
Notion Roadmap Importer Module

This module handles importing roadmap data into Notion with proper hierarchical structure
using the Notion API. It creates pages for each roadmap item and sets up parent-child relationships.
"""

import os
import csv
import time
from typing import Dict, List, Optional
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NotionImporter:
    def __init__(self):
        """Initialize the Notion client and configuration."""
        self.notion = Client(auth=os.getenv("NOTION_TOKEN"))
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self.parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID")
        
        # Store created pages for relationship mapping
        self.created_pages: Dict[str, str] = {}
        self.roadmap_items: List[Dict] = []
        
        # Rate limiting
        self.request_delay = 0.05  # 50ms between requests
        
    def load_roadmap_data(self, csv_file: str) -> None:
        """Load roadmap data from CSV file."""
        print(f"Loading roadmap data from {csv_file}...")
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            self.roadmap_items = list(reader)
            
        print(f"Loaded {len(self.roadmap_items)} roadmap items")
    
    def create_database(self, container_page_id: str) -> str:
        """Create the main roadmap database in Notion within the container page."""
        print("Creating roadmap database...")
        
        # Create database without self-referencing relation first
        database_properties = {
            "Name": {"title": {}},
            "Type": {
                "select": {
                    "options": [
                        {"name": "Project", "color": "purple"},
                        {"name": "Milestone", "color": "blue"},
                        {"name": "Epic", "color": "green"},
                        {"name": "Story", "color": "orange"},
                        {"name": "Task", "color": "red"},
                    ]
                }
            },
            "Duration (hours)": {"number": {"format": "number"}},
            "Priority": {
                "select": {
                    "options": [
                        {"name": "Critical", "color": "red"},
                        {"name": "High", "color": "orange"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "gray"},
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Not Started", "color": "gray"},
                        {"name": "In Progress", "color": "blue"},
                        {"name": "Completed", "color": "green"},
                        {"name": "Blocked", "color": "red"},
                    ]
                }
            },
            "Goal/Description": {"rich_text": {}},
            "Benefits": {"rich_text": {}},
            "Prerequisites": {"rich_text": {}},
            "Technical Requirements": {"rich_text": {}},
            "Claude Code Prompt": {"rich_text": {}},
        }
        
        response = self.notion.databases.create(
            parent={"page_id": container_page_id},
            title=[{"type": "text", "text": {"content": "📊 Roadmap Database"}}],
            properties=database_properties
        )
        
        database_id = response["id"]
        
        # Add the Parent relation as self-referencing after database creation
        self.notion.databases.update(
            database_id=database_id,
            properties={
                "Parent": {
                    "relation": {
                        "database_id": database_id,
                        "single_property": {}
                    }
                }
            }
        )
        
        print(f"Created database with ID: {database_id}")
        return database_id
    
    def create_page_content(self, item: Dict) -> List[Dict]:
        """Generate rich content blocks for a roadmap item page."""
        content_blocks = []
        
        # Overview section
        overview_props = []
        if item.get("Type"):
            overview_props.append(f"**Type:** {item['Type']}")
        if item.get("Duration"):
            overview_props.append(f"**Duration:** {item['Duration']} hours")
        if item.get("Priority"):
            overview_props.append(f"**Priority:** {item['Priority']}")
        if item.get("Status"):
            overview_props.append(f"**Status:** {item['Status']}")
        
        if overview_props:
            content_blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "📋 Overview"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "\n".join(overview_props)}}]
                    }
                }
            ])
        
        # Description section
        if item.get("Goal/Description"):
            content_blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "🎯 Description"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": item["Goal/Description"]}}]
                    }
                }
            ])
        
        # Benefits section
        if item.get("Benefits"):
            content_blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "✅ Benefits"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": item["Benefits"]}}]
                    }
                }
            ])
        
        # Prerequisites section
        if item.get("Prerequisites"):
            content_blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "📚 Prerequisites"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": item["Prerequisites"]}}]
                    }
                }
            ])
        
        # Technical Requirements section
        if item.get("Technical Requirements"):
            content_blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "🔧 Technical Requirements"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": item["Technical Requirements"]}}]
                    }
                }
            ])
        
        # Claude Code Prompt section
        if item.get("Claude Code Prompt"):
            content_blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "🤖 Claude Code Prompt"}}]
                }
            })
            
            # Split long prompts if needed
            prompt_content = item["Claude Code Prompt"]
            chunk_size = 1900
            
            if len(prompt_content) <= chunk_size:
                content_blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": prompt_content}}],
                        "language": "plain text"
                    }
                })
            else:
                chunks = [prompt_content[i:i+chunk_size] for i in range(0, len(prompt_content), chunk_size)]
                for chunk in chunks:
                    content_blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{"type": "text", "text": {"content": chunk}}],
                            "language": "plain text"
                        }
                    })
        
        # Notes section
        content_blocks.extend([
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "📝 Notes"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "Space for updates, blockers, and additional notes."}}]
                }
            }
        ])
        
        return content_blocks
    
    def create_database_pages(self) -> None:
        """Create pages in the database for all roadmap items."""
        print("Creating database pages...")
        
        for i, item in enumerate(self.roadmap_items):
            print(f"Creating page {i+1}/{len(self.roadmap_items)}: {item['Name']}")
            
            # Prepare page properties
            type_emojis = {
                "Project": "🎯",
                "Milestone": "🏁", 
                "Epic": "📦",
                "Story": "📖",
                "Task": "✅"
            }
            
            item_emoji = type_emojis.get(item.get("Type", ""), "📄")
            
            properties = {
                "Name": {
                    "title": [{"type": "text", "text": {"content": item['Name']}}]
                },
                "Type": {
                    "select": {"name": item["Type"]} if item.get("Type") else None
                },
                "Status": {
                    "select": {"name": item["Status"]} if item.get("Status") else None
                }
            }
            
            # Add optional properties
            if item.get("Duration"):
                try:
                    properties["Duration (hours)"] = {"number": int(item["Duration"])}
                except (ValueError, KeyError):
                    pass
            
            if item.get("Priority"):
                properties["Priority"] = {"select": {"name": item["Priority"]}}
            
            if item.get("Goal/Description"):
                properties["Goal/Description"] = {
                    "rich_text": [{"type": "text", "text": {"content": item["Goal/Description"][:2000]}}]
                }
            
            if item.get("Benefits"):
                properties["Benefits"] = {
                    "rich_text": [{"type": "text", "text": {"content": item["Benefits"][:2000]}}]
                }
            
            if item.get("Prerequisites"):
                properties["Prerequisites"] = {
                    "rich_text": [{"type": "text", "text": {"content": item["Prerequisites"][:2000]}}]
                }
            
            if item.get("Technical Requirements"):
                properties["Technical Requirements"] = {
                    "rich_text": [{"type": "text", "text": {"content": item["Technical Requirements"][:2000]}}]
                }
            
            if item.get("Claude Code Prompt"):
                properties["Claude Code Prompt"] = {
                    "rich_text": [{"type": "text", "text": {"content": item["Claude Code Prompt"][:2000]}}]
                }
            
            # Create the page
            try:
                response = self.notion.pages.create(
                    parent={"database_id": self.database_id},
                    icon={"type": "emoji", "emoji": item_emoji},
                    properties=properties,
                    children=self.create_page_content(item)
                )
                
                self.created_pages[item["Name"]] = response["id"]
                print(f"✅ Created: {item['Name']}")
                
                # Rate limiting
                time.sleep(self.request_delay)
                
            except Exception as e:
                print(f"Error creating page for {item['Name']}: {e}")
                continue
    
    def set_parent_relationships(self) -> None:
        """Set up parent-child relationships between pages."""
        print("Setting up parent-child relationships...")
        
        for item in self.roadmap_items:
            if (item.get("Parent") and 
                item["Parent"] in self.created_pages and 
                item["Name"] in self.created_pages):
                page_id = self.created_pages[item["Name"]]
                parent_id = self.created_pages[item["Parent"]]
                
                print(f"Setting parent: {item['Name']} -> {item['Parent']}")
                
                try:
                    self.notion.pages.update(
                        page_id=page_id,
                        properties={
                            "Parent": {
                                "relation": [{"id": parent_id}]
                            }
                        }
                    )
                    
                    time.sleep(self.request_delay)
                    
                except Exception as e:
                    print(f"Error setting parent for {item['Name']}: {e}")
    
    def run_import(self, csv_file: str) -> None:
        """Run the complete import process."""
        print("🚀 Starting Roadmap Import...")
        
        # Load data
        self.load_roadmap_data(csv_file)
        
        # Create database if not provided
        if not self.database_id:
            if not self.parent_page_id:
                print("❌ Error: NOTION_PARENT_PAGE_ID is required when creating a new database")
                return
            self.database_id = self.create_database(self.parent_page_id)
        
        # Create all pages
        self.create_database_pages()
        
        # Set up relationships
        self.set_parent_relationships()
        
        print("✅ Import completed successfully!")
        print(f"🔗 Database URL: https://notion.so/{self.database_id.replace('-', '')}")
        print(f"📊 Created {len(self.created_pages)} pages")

def main():
    """CLI entry point"""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m roadmap_notion.importer <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    importer = NotionImporter()
    importer.run_import(csv_file)

if __name__ == "__main__":
    main()