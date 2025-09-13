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
    
    def create_overview_page(self) -> str:
        """Create a comprehensive overview page for the roadmap."""
        print("Creating roadmap overview page...")
        
        # Count items by type
        type_counts = {}
        for item in self.roadmap_items:
            item_type = item.get("Type", "Unknown")
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        # Build hierarchical table of contents
        toc_blocks = []
        
        # Group items by parent for hierarchical display
        items_by_parent = {}
        for item in self.roadmap_items:
            parent = item.get("Parent", "")
            if parent not in items_by_parent:
                items_by_parent[parent] = []
            items_by_parent[parent].append(item)
        
        def add_toc_items(parent_name: str, indent_level: int = 0):
            """Recursively add table of contents items"""
            if parent_name not in items_by_parent:
                return
            
            # Sort items by type hierarchy
            type_order = {"Project": 0, "Milestone": 1, "Epic": 2, "Story": 3, "Task": 4}
            items = sorted(items_by_parent[parent_name], 
                         key=lambda x: (type_order.get(x.get("Type", ""), 5), x["Name"]))
            
            for item in items:
                indent = "  " * indent_level
                item_type = item.get("Type", "")
                duration = f" ({item['Duration']}h)" if item.get("Duration") else ""
                
                # Create linked text if page exists
                if item["Name"] in self.created_pages:
                    page_id = self.created_pages[item["Name"]]
                    toc_blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"type": "text", "text": {"content": f"{indent}• "}},
                                {
                                    "type": "mention",
                                    "mention": {"page": {"id": page_id}},
                                    "href": f"https://www.notion.so/{page_id.replace('-', '')}"
                                },
                                {"type": "text", "text": {"content": f" ({item_type}){duration}"}}
                            ]
                        }
                    })
                else:
                    toc_blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": f"{indent}• {item['Name']} ({item_type}){duration}"}}]
                        }
                    })
                
                # Recursively add children
                add_toc_items(item["Name"], indent_level + 1)
        
        # Start with root items (no parent)
        add_toc_items("", 0)
        
        # Build overview page content
        overview_content = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": "🗺️ Project Roadmap Overview"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "This comprehensive roadmap outlines the complete development journey for your project. It's organized hierarchically from high-level milestones down to specific implementation tasks."}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "📊 Roadmap Statistics"}}]
                }
            }
        ]
        
        # Add statistics
        stats_text = f"**Total Items:** {len(self.roadmap_items)}\n\n"
        for item_type in ["Project", "Milestone", "Epic", "Story", "Task"]:
            if item_type in type_counts:
                stats_text += f"**{item_type}s:** {type_counts[item_type]}\n"
        
        overview_content.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": stats_text}}]
            }
        })
        
        # Add quick access section
        overview_content.extend([
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "🔗 Quick Access"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "📋 "}},
                        {
                            "type": "mention",
                            "mention": {"database": {"id": self.database_id}},
                            "href": f"https://www.notion.so/{self.database_id.replace('-', '')}"
                        },
                        {"type": "text", "text": {"content": " - Complete Roadmap Database"}}
                    ]
                }
            }
        ])
        
        # Add table of contents
        overview_content.extend([
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "📑 Complete Table of Contents"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "Below is the complete hierarchical structure of your roadmap with links to each item:"}}]
                }
            }
        ])
        
        # Add TOC items (limit to first 90 to avoid API limits)
        overview_content.extend(toc_blocks[:90])
        
        if len(toc_blocks) > 90:
            overview_content.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"... and {len(toc_blocks) - 90} more items (see the database for complete list)"}}]
                }
            })
        
        # Add implementation notes
        overview_content.extend([
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "💡 Implementation Notes"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "This roadmap includes detailed Claude Code prompts for each task, making it easy to implement features using AI assistance. Each task contains specific technical requirements, implementation guidance, and acceptance criteria."}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "The roadmap follows a milestone-based approach with clear dependencies and hierarchical organization from Projects → Milestones → Epics → Stories → Tasks."}}]
                }
            }
        ])
        
        # Create the overview page
        response = self.notion.pages.create(
            parent={"page_id": self.parent_page_id},
            icon={"type": "emoji", "emoji": "🗺️"},
            properties={
                "title": [{"type": "text", "text": {"content": "📋 Roadmap Overview"}}]
            },
            children=overview_content[:100]  # Limit to 100 blocks
        )
        
        overview_page_id = response["id"]
        print(f"✅ Created overview page (ID: {overview_page_id})")
        
        # Add remaining blocks if needed
        if len(overview_content) > 100:
            remaining_blocks = overview_content[100:]
            batch_size = 100
            for i in range(0, len(remaining_blocks), batch_size):
                batch = remaining_blocks[i:i + batch_size]
                try:
                    self.notion.blocks.children.append(
                        block_id=overview_page_id,
                        children=batch
                    )
                except Exception as e:
                    print(f"  Warning: Could not add some overview blocks: {e}")
                    break
        
        return overview_page_id

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
        
        # Create overview page
        overview_page_id = self.create_overview_page()
        
        print("✅ Import completed successfully!")
        print(f"🔗 Database URL: https://notion.so/{self.database_id.replace('-', '')}")
        print(f"📄 Overview Page: https://notion.so/{overview_page_id.replace('-', '')}")
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