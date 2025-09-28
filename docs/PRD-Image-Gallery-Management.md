# Product Requirements Document (PRD)
## BookStack MCP Image Gallery Management Tools

**Version:** 1.1  
**Date:** 2025-09-27  
**Status:** In Implementation  
**Owner:** Development Team  

---

## 📋 Executive Summary

Design and implement consolidated image management tools for the BookStack MCP that provide complete image lifecycle management while minimizing tool proliferation through intelligent consolidation.

### Key Objectives
- ✅ Enable complete image workflow within MCP
- ✅ Reduce tool count from 5 to 2 (60% reduction)
- ✅ Maintain 100% API coverage for Image Gallery endpoints
- ✅ Provide superior developer experience

---

## 🎯 Problem Statement

### Current State
- Book/content creation supports `image_id` parameter but no way to manage images
- Users must use BookStack web interface for image operations  
- Missing 5 separate Image Gallery API endpoints creates workflow gaps

### Pain Points
1. **Broken Workflow**: Can reference images but can't create/manage them
2. **Tool Proliferation**: Traditional approach would create 5+ separate tools
3. **Poor UX**: Multiple tools for related operations increases complexity
4. **Maintenance Burden**: More tools = more code to maintain and test

---

## 💡 Solution Strategy

### Core Principle: **Functional Consolidation Over Endpoint Mapping**

Instead of creating 5 separate tools (list, create, read, update, delete), design **2 consolidated tools** that handle complete workflows:

1. **`bookstack_manage_images`** - Unified CRUD operations
2. **`bookstack_search_images`** - Advanced search and discovery

### Benefits
- **Reduced Complexity**: 60% fewer tools to learn and maintain
- **Better UX**: Single tool for complete workflows
- **Consistent Interface**: Uniform response formats
- **Future-Proof**: Pattern applicable to other feature sets

---

## 🛠 Tool Specifications

### Tool 1: `bookstack_manage_images`

**Purpose:** Single tool for all image lifecycle operations

#### Input Schema
```typescript
interface ImageManagementInput {
  operation: 'create' | 'read' | 'update' | 'delete' | 'list';
  
  // For create operations
  name?: string;
  image?: File | string; // File object or base64 string
  
  // For read/update/delete operations  
  id?: number;
  
  // For update operations
  new_name?: string;
  new_image?: File | string;
  
  // For list operations
  offset?: number;
  count?: number;
  sort?: string;
  filter?: Record<string, string>;
}
```

#### Usage Examples
```typescript
// Create new image
await bookstackManageImages({
  operation: 'create',
  name: 'book-cover.jpg',
  image: fileObject
});

// List images with pagination
await bookstackManageImages({
  operation: 'list',
  count: 20,
  offset: 0,
  filters: [
    { key: 'uploaded_to', value: '12' }
  ]
});

// Update existing image
await bookstackManageImages({
  operation: 'update', 
  id: 123,
  new_name: 'updated-cover.jpg'
});

// Delete image
await bookstackManageImages({
  operation: 'delete',
  id: 123
});

// Get image details
await bookstackManageImages({
  operation: 'read',
  id: 123
});
```

### Tool 2: `bookstack_search_images`

**Purpose:** Advanced image discovery and filtering

#### Input Schema
```typescript
interface ImageSearchInput {
  query?: string;           // Search by name/description
  extension?: string;       // Filter by file type (.jpg, .png, etc.)
  size_min?: number;        // Minimum file size in bytes
  size_max?: number;        // Maximum file size in bytes
  created_after?: string;   // ISO date string
  created_before?: string;  // ISO date string
  used_in?: 'books' | 'pages' | 'chapters'; // Usage filtering
  count?: number;           // Results per page (default: 20, max: 100)
  offset?: number;          // Pagination offset
}
```

#### Usage Examples
```typescript
// Search for book cover images
await bookstackSearchImages({
  query: 'cover',
  extension: '.jpg',
  used_in: 'books'
});

// Find large images
await bookstackSearchImages({
  size_min: 1000000, // 1MB+
  count: 10
});

// Recent images
await bookstackSearchImages({
  created_after: '2025-01-01',
  sort: '-created_at'
});
```

---

## 🚀 Implementation Update (September 2025)

- ✅ `bookstack_manage_images` now supports full CRUD with multipart uploads and transparent base64/data-URL decoding.
- ✅ `bookstack_search_images` delivers the consolidated discovery workflow with extension, date, and size filters.
- ✅ Unified response envelope `{ operation, success, data, metadata }` adopted across both tools.
- ✅ List operations use a 30s smart cache to keep repeated queries under the 2s latency goal while auto-invalidation follows create/update/delete.
- ✅ Zod validation enforces mutually exclusive update payloads and guards size/date ranges for search.
- ✅ Unit coverage expanded via Vitest (see `bookstack-tools.test.ts`) covering base64 upload handling, caching, and advanced query mapping.

**Tracking:** BSPJ-8 (CRUD tool), BSPJ-9 (search & base64 enhancements), BSPJ-10 (caching, validation, docs) in Huly.

---

## 🏗 Technical Implementation

### File Upload Handling Strategy

```typescript
class ImageManagementTool extends BookstackTool<ImageManagementInput> {
  async execute(input: ImageManagementInput) {
    switch (input.operation) {
      case 'create': return this.createImage(input);
      case 'list': return this.listImages(input);
      case 'read': return this.readImage(input);
      case 'update': return this.updateImage(input);
      case 'delete': return this.deleteImage(input);
    }
  }

  private async createImage(input: ImageManagementInput) {
    const formData = new FormData();
    formData.append('name', input.name!);
    
    // Handle different image input types
    if (input.image instanceof File) {
      formData.append('image', input.image);
    } else if (typeof input.image === 'string') {
      // Handle base64 or URL
      const blob = this.convertToBlob(input.image);
      formData.append('image', blob);
    }
    
    return this.postRequest('/api/image-gallery', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }
}
```

### Response Standardization

All operations return consistent response format:

```typescript
interface ImageManagementResponse {
  operation: string;
  success: boolean;
  data: ImageData | ImageData[] | null;
  metadata?: {
    total?: number;
    count?: number;
    offset?: number;
  };
}
```

---

## 📊 Success Metrics

### Quantitative Goals
- **Tool Count Reduction**: 5 tools → 2 tools (60% reduction)
- **API Coverage**: 100% of Image Gallery endpoints
- **Response Time**: <2s for image operations
- **Error Rate**: <1% for valid operations
- **Test Coverage**: >95% for both tools

### Qualitative Goals
- **Developer Experience**: Single tool for complete workflows
- **Maintainability**: Consolidated logic, easier to maintain
- **Consistency**: Uniform response formats across operations
- **Documentation**: Clear examples for all use cases

---

## 📅 Implementation Timeline

### Phase 1: Core Image Management (Week 1)
- [x] Implement `bookstack_manage_images` tool
- [x] Support all 5 CRUD operations
- [x] Basic file upload handling (File objects)
- [x] Unit tests for all operations
- [x] Basic error handling

### Phase 2: Advanced Features (Week 2)
- [x] Implement `bookstack_search_images` tool
- [x] Add base64 image support
- [x] Enhanced error handling and validation
- [ ] Integration tests with real BookStack instance
- [ ] Performance optimization

### Phase 3: Polish & Documentation (Week 3)
- [x] Response caching for list operations
- [x] Advanced validation and error messages
- [x] Comprehensive documentation with examples
- [ ] Code review and refactoring
- [ ] Release preparation

---

## ⚠️ Risk Assessment

### Technical Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| File Upload Complexity | High | Medium | Support multiple input formats (File, base64, URL) |
| Large File Handling | Medium | Low | Implement file size validation and streaming |
| Schema Complexity | Medium | Medium | Operation-specific validation with clear errors |

### UX Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Tool Complexity | Medium | Low | Clear documentation with examples |
| Learning Curve | Low | Medium | Helper methods for common operations |

---

## 🔮 Future Considerations

### Extensibility Opportunities
- Apply pattern to other consolidated tools (attachments, permissions)
- Framework for operation-based tool design
- Auto-generated documentation from schemas

### Advanced Features (Future Releases)
- Batch operations (upload multiple images)
- Image transformation (resize, crop, optimize)
- Usage analytics (track which images are used where)
- Image versioning and history
- CDN integration for performance

---

## 📚 Appendix

### API Endpoint Mapping
| Operation | HTTP Method | Endpoint | Status |
|-----------|-------------|----------|---------|
| List | GET | `/api/image-gallery` | ✅ Planned |
| Create | POST | `/api/image-gallery` | ✅ Planned |
| Read | GET | `/api/image-gallery/{id}` | ✅ Planned |
| Update | PUT | `/api/image-gallery/{id}` | ✅ Planned |
| Delete | DELETE | `/api/image-gallery/{id}` | ✅ Planned |

### Dependencies
- BookStack API v1.0+
- MCP Framework v0.2.15+
- Zod validation library
- Undici HTTP client
- FormData support for file uploads

---

**Document Status:** Ready for Implementation  
**Next Review:** After Phase 1 completion  
**Stakeholders:** Development Team, Product Owner, QA Team
