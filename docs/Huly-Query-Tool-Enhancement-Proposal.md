# Huly Query Tool Enhancement Proposal

**Version:** 1.0  
**Date:** 2025-10-02  
**Purpose:** Define ideal data structures for Huly query responses to improve AI assistant workflows

---

## 📋 Executive Summary

This document outlines the data fields that would be most valuable when querying Huly entities (projects, components, milestones, issues, templates, comments). The goal is to provide comprehensive metadata that enables better decision-making, reduces follow-up queries, and improves the overall developer experience.

---

## 🎯 Core Principles

1. **Completeness** - Include all relevant metadata in a single query response
2. **Actionability** - Provide IDs and identifiers needed for subsequent operations
3. **Context** - Include relational data (counts, associations, ownership)
4. **Temporal Awareness** - Show creation, modification, and due dates
5. **Discoverability** - Make it easy to understand entity relationships

---

## 📊 Entity-Specific Data Requirements

### 1. **Projects**

#### Current Data Returned
```json
{
  "identifier": "BKMCP",
  "name": "BookStack MCP",
  "description": "...",
  "archived": false,
  "private": false,
  "owners": [],
  "createdOn": 1759379274970,
  "modifiedOn": 1759379274970
}
```

#### Desired Additional Fields
```json
{
  "id": "68ddff4add06f8de011dbf3f",           // ✨ Project ID for operations
  "identifier": "BKMCP",
  "name": "BookStack MCP",
  "description": "...",
  "archived": false,
  "private": false,
  
  // Ownership & Team
  "owners": [
    {
      "id": "user_123",
      "name": "John Doe",
      "email": "john@example.com"
    }
  ],
  "members": [                                  // ✨ Team members
    {
      "id": "user_456",
      "name": "Jane Smith",
      "email": "jane@example.com",
      "role": "contributor"
    }
  ],
  
  // Temporal Data
  "createdOn": 1759379274970,
  "createdBy": "user_123",                      // ✨ Creator ID
  "modifiedOn": 1759379274970,
  "modifiedBy": "user_456",                     // ✨ Last modifier
  
  // Statistics & Counts
  "stats": {                                    // ✨ Project statistics
    "totalIssues": 42,
    "openIssues": 15,
    "closedIssues": 27,
    "totalComponents": 8,
    "totalMilestones": 3,
    "activeMilestones": 2
  },
  
  // Settings
  "defaultAssignee": "user_123",               // ✨ Default assignee
  "defaultPriority": "medium",                 // ✨ Default priority
  "issuePrefix": "BKMCP",                      // ✨ Issue identifier prefix
  
  // URLs
  "url": "https://huly.app/project/BKMCP"      // ✨ Direct link to project
}
```

---

### 2. **Components**

#### Current Data Returned
```json
{
  "label": "Image Gallery",
  "description": "Image management tools..."
}
```

#### Desired Complete Structure
```json
{
  "id": "68de7759dd06f8de011dbf53",           // ✨ Component ID (critical for delete/update)
  "label": "Image Gallery",
  "description": "Image management tools...",
  "projectId": "68ddff4add06f8de011dbf3f",     // ✨ Parent project ID
  "projectIdentifier": "BKMCP",                // ✨ Parent project identifier
  
  // Temporal Data
  "createdOn": 1759379500000,                  // ✨ Creation timestamp
  "createdBy": "user_123",                     // ✨ Creator
  "modifiedOn": 1759379500000,                 // ✨ Last modified
  "modifiedBy": "user_123",                    // ✨ Last modifier
  
  // Statistics
  "stats": {                                   // ✨ Component usage stats
    "totalIssues": 12,
    "openIssues": 5,
    "closedIssues": 7,
    "issuesInProgress": 3
  },
  
  // Associations
  "lead": {                                    // ✨ Component lead/owner
    "id": "user_123",
    "name": "John Doe"
  },
  
  // Status
  "archived": false,                           // ✨ Archive status
  
  // URLs
  "url": "https://huly.app/project/BKMCP/component/image-gallery"
}
```

---

### 3. **Milestones**

#### Current Data Returned
```json
{
  "label": "v1.0 Release",
  "description": "First stable release",
  "targetDate": "2025-12-31",
  "status": "in-progress"
}
```

#### Desired Complete Structure
```json
{
  "id": "milestone_789",                       // ✨ Milestone ID
  "label": "v1.0 Release",
  "description": "First stable release",
  "projectId": "68ddff4add06f8de011dbf3f",     // ✨ Parent project
  "projectIdentifier": "BKMCP",
  
  // Timeline
  "targetDate": "2025-12-31",                  // Target completion
  "startDate": "2025-09-01",                   // ✨ Start date
  "completedDate": null,                       // ✨ Actual completion (if done)
  
  // Status
  "status": "in-progress",                     // planned, in-progress, completed, blocked
  "progress": 65,                              // ✨ Percentage complete (0-100)
  
  // Temporal
  "createdOn": 1759379600000,
  "createdBy": "user_123",
  "modifiedOn": 1759379700000,
  "modifiedBy": "user_456",
  
  // Statistics
  "stats": {                                   // ✨ Milestone progress
    "totalIssues": 20,
    "completedIssues": 13,
    "openIssues": 5,
    "blockedIssues": 2,
    "estimatedHours": 160,
    "actualHours": 104
  },
  
  // Health Indicators
  "health": {                                  // ✨ Milestone health
    "status": "at-risk",                       // on-track, at-risk, delayed
    "daysRemaining": 45,
    "burndownRate": 0.65
  },
  
  // URLs
  "url": "https://huly.app/project/BKMCP/milestone/v1.0"
}
```

---

### 4. **Issues**

#### Current Data Returned (Minimal)
```json
{
  "identifier": "BKMCP-123",
  "title": "Implement image upload",
  "status": "in-progress"
}
```

#### Desired Complete Structure
```json
{
  "id": "issue_abc123",                        // ✨ Issue ID
  "identifier": "BKMCP-123",                   // Issue identifier
  "title": "Implement image upload",
  "description": "Add support for uploading images...",
  
  // Project Context
  "projectId": "68ddff4add06f8de011dbf3f",
  "projectIdentifier": "BKMCP",
  
  // Classification
  "component": {                               // ✨ Associated component
    "id": "68de7759dd06f8de011dbf53",
    "label": "Image Gallery"
  },
  "milestone": {                               // ✨ Associated milestone
    "id": "milestone_789",
    "label": "v1.0 Release"
  },
  
  // Status & Priority
  "status": "in-progress",                     // backlog, todo, in-progress, review, done
  "priority": "high",                          // low, medium, high, urgent
  "type": "feature",                           // ✨ bug, feature, task, epic
  
  // Assignment
  "assignee": {                                // ✨ Current assignee
    "id": "user_123",
    "name": "John Doe",
    "email": "john@example.com"
  },
  "reporter": {                                // ✨ Issue creator
    "id": "user_456",
    "name": "Jane Smith",
    "email": "jane@example.com"
  },
  
  // Temporal
  "createdOn": 1759379800000,
  "modifiedOn": 1759380000000,
  "dueDate": "2025-11-15",                     // ✨ Due date
  "resolvedOn": null,                          // ✨ Resolution timestamp
  
  // Estimation & Tracking
  "estimation": 8,                             // ✨ Estimated hours
  "timeSpent": 5,                              // ✨ Actual hours logged
  "remainingTime": 3,                          // ✨ Remaining estimate
  
  // Relationships
  "parentIssue": "BKMCP-100",                  // ✨ Parent issue (for sub-issues)
  "subIssues": [                               // ✨ Child issues
    "BKMCP-124",
    "BKMCP-125"
  ],
  "blockedBy": ["BKMCP-120"],                  // ✨ Blocking issues
  "blocks": ["BKMCP-130"],                     // ✨ Issues this blocks
  "relatedIssues": ["BKMCP-115"],              // ✨ Related issues
  
  // Engagement
  "stats": {                                   // ✨ Engagement metrics
    "comments": 7,
    "attachments": 3,
    "watchers": 4,
    "votes": 12
  },
  
  // Tags & Labels
  "tags": [                                    // ✨ Custom tags
    { "name": "backend", "value": "api" },
    { "name": "priority", "value": "p1" }
  ],
  
  // URLs
  "url": "https://huly.app/project/BKMCP/issue/BKMCP-123"
}
```

---

### 5. **Templates**

#### Desired Complete Structure
```json
{
  "id": "template_xyz",                        // ✨ Template ID
  "title": "Bug Report Template",
  "description": "Standard template for bug reports",
  
  // Project Context
  "projectId": "68ddff4add06f8de011dbf3f",
  "projectIdentifier": "BKMCP",
  
  // Template Configuration
  "defaultPriority": "medium",
  "defaultComponent": "Image Gallery",
  "defaultAssignee": "user_123",
  "defaultEstimation": 4,
  
  // Template Content
  "descriptionTemplate": "## Steps to Reproduce\n1. ...",
  
  // Child Templates
  "children": [                                // ✨ Sub-task templates
    {
      "title": "Investigate root cause",
      "priority": "high",
      "estimation": 2
    },
    {
      "title": "Write fix",
      "priority": "medium",
      "estimation": 4
    }
  ],
  
  // Usage Statistics
  "stats": {                                   // ✨ Template usage
    "timesUsed": 45,
    "lastUsed": 1759380000000,
    "averageCompletionTime": 72  // hours
  },
  
  // Temporal
  "createdOn": 1759379900000,
  "createdBy": "user_123",
  "modifiedOn": 1759380100000,
  "modifiedBy": "user_456",
  
  // URLs
  "url": "https://huly.app/project/BKMCP/template/bug-report"
}
```

---

### 6. **Comments**

#### Desired Complete Structure
```json
{
  "id": "comment_123",                         // ✨ Comment ID
  "message": "This looks good, approved!",
  
  // Context
  "issueId": "issue_abc123",
  "issueIdentifier": "BKMCP-123",
  
  // Author
  "author": {                                  // ✨ Comment author
    "id": "user_456",
    "name": "Jane Smith",
    "email": "jane@example.com",
    "avatar": "https://..."
  },
  
  // Temporal
  "createdOn": 1759380200000,
  "modifiedOn": 1759380300000,                 // ✨ If edited
  "isEdited": true,                            // ✨ Edit flag
  
  // Content Type
  "format": "markdown",                        // ✨ markdown, plain, html
  
  // Engagement
  "reactions": [                               // ✨ Emoji reactions
    { "emoji": "👍", "count": 5, "users": ["user_123", "user_789"] },
    { "emoji": "🎉", "count": 2, "users": ["user_456"] }
  ],
  
  // Attachments
  "attachments": [                             // ✨ File attachments
    {
      "id": "file_001",
      "name": "screenshot.png",
      "size": 245678,
      "mimeType": "image/png",
      "url": "https://..."
    }
  ],
  
  // Threading
  "parentCommentId": null,                     // ✨ For threaded replies
  "replies": [],                               // ✨ Reply comment IDs
  
  // URLs
  "url": "https://huly.app/project/BKMCP/issue/BKMCP-123#comment-123"
}
```

---

## 🔧 Query Options Enhancement

### Proposed Query Parameters

```typescript
interface QueryOptions {
  // Pagination
  limit?: number;           // Max results (current: supported)
  offset?: number;          // Skip results (current: supported)
  
  // Sorting
  sort?: string;            // e.g., "-createdOn", "priority" (current: supported)
  
  // Field Selection
  fields?: string[];        // ✨ NEW: Select specific fields to return
  includeStats?: boolean;   // ✨ NEW: Include statistics (default: true)
  includeRelations?: boolean; // ✨ NEW: Include related entities (default: false)
  
  // Filtering
  filters?: {               // Enhanced filtering
    status?: string[];
    priority?: string[];
    assignee?: string[];
    component?: string[];
    milestone?: string[];
    createdAfter?: string;
    createdBefore?: string;
    modifiedAfter?: string;
    modifiedBefore?: string;
    tags?: Record<string, string>;
  };
  
  // Search
  searchQuery?: string;     // ✨ NEW: Full-text search within results
  
  // Grouping
  groupBy?: string;         // ✨ NEW: Group results by field
}
```

---

## 📈 Benefits of Enhanced Data

### 1. **Reduced API Calls**
- Get all needed information in one query instead of multiple follow-ups
- Example: Component list with IDs eliminates need for individual reads before delete

### 2. **Better Decision Making**
- Statistics help prioritize which components/milestones need attention
- Health indicators show project status at a glance

### 3. **Improved UX**
- Direct URLs enable quick navigation
- Rich metadata provides context without additional queries

### 4. **Efficient Operations**
- Having IDs readily available enables immediate CRUD operations
- Relationship data (parent/child issues) enables better planning

### 5. **Analytics & Reporting**
- Usage statistics help identify patterns
- Temporal data enables trend analysis

---

## 🎯 Priority Recommendations

### **High Priority** (Critical for basic workflows)
1. ✅ Include entity IDs in all list responses
2. ✅ Add creation and modification timestamps
3. ✅ Include basic statistics (issue counts, etc.)
4. ✅ Add parent/project context for all entities

### **Medium Priority** (Significantly improves UX)
1. Include assignee/owner information
2. Add relationship data (parent/child, blocking)
3. Include component and milestone associations for issues
4. Add progress/health indicators

### **Low Priority** (Nice to have)
1. Engagement metrics (reactions, watchers)
2. Usage statistics for templates
3. Direct URLs to entities
4. Advanced filtering options

---

## 📝 Implementation Notes

1. **Backward Compatibility**: New fields should be additive, not breaking existing responses
2. **Performance**: Consider lazy-loading expensive fields (stats, relations) via `includeStats` flag
3. **Consistency**: Use same field names across all entity types (e.g., `createdOn`, not `created_at`)
4. **Documentation**: Update tool descriptions to reflect available fields

---

**Next Steps:** Review with Huly MCP tool maintainers and prioritize implementation based on user feedback.

