/**
 * Tool handler for searching content in BookStack
 * Searches across shelves, books, chapters, and pages
 */
export async function handleSearchBookstack(server, args) {
    try {
        // Validate arguments
        if (!args.query || typeof args.query !== 'string' || !args.query.trim()) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Valid search query is required" }, null, 2),
                }],
                isError: true
            };
        }

        // Validate optional pagination parameters
        if (args.page !== undefined) {
            if (typeof args.page !== 'number' || args.page < 1) {
                return {
                    content: [{
                        type: 'text',
                        text: JSON.stringify({ error: "Page must be a positive number" }, null, 2),
                    }],
                    isError: true
                };
            }
        }

        if (args.count !== undefined) {
            if (typeof args.count !== 'number' || args.count < 1 || args.count > 100) {
                return {
                    content: [{
                        type: 'text',
                        text: JSON.stringify({ error: "Count must be a positive number (max 100)" }, null, 2),
                    }],
                    isError: true
                };
            }
        }

        // Get environment variables with fallbacks
        const baseUrl = process.env.BS_URL || "https://knowledge.oculair.ca";
        const tokenId = process.env.BS_TOKEN_ID || "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT";
        const tokenSecret = process.env.BS_TOKEN_SECRET || "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE";

        if (!tokenId || !tokenSecret) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "BS_TOKEN_ID and BS_TOKEN_SECRET environment variables must be set" }, null, 2),
                }],
                isError: true
            };
        }

        console.log(`Searching BookStack at ${baseUrl} with query: "${args.query}"`);

        // Set up request headers
        const headers = {
            'Authorization': `Token ${tokenId}:${tokenSecret}`,
            'Content-Type': 'application/json'
        };

        // Build query parameters
        const searchParams = new URLSearchParams({
            query: args.query.trim()
        });

        if (args.page !== undefined) {
            searchParams.append('page', args.page.toString());
        }

        if (args.count !== undefined) {
            searchParams.append('count', args.count.toString());
        }

        // Make the API request
        const apiUrl = `${baseUrl.replace(/\/$/, '')}/api/search?${searchParams.toString()}`;
        console.log(`Making request to: ${apiUrl}`);

        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: headers,
            timeout: 30000
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`BookStack API error: ${response.status} - ${errorText}`);
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ 
                        error: `BookStack API error: ${response.status} - ${response.statusText}`,
                        details: errorText
                    }, null, 2),
                }],
                isError: true
            };
        }

        const data = await response.json();
        console.log(`Search completed. Found ${data.total || 0} results`);

        // Process and simplify the results
        const simplifiedResults = [];
        
        if (data.data && Array.isArray(data.data)) {
            for (const item of data.data) {
                // Extract basic info
                const title = item.name || 'Untitled';
                const url = item.url || '';
                const itemType = item.type || 'unknown';
                const id = item.id || null;
                
                // Try to get a summary from preview_html content
                let summary = "";
                if (item.preview_html && item.preview_html.content) {
                    // Clean up HTML tags and get first sentence
                    let content = item.preview_html.content;
                    // Remove HTML tags
                    content = content.replace(/<[^>]+>/g, '');
                    // Get first sentence or first 150 chars
                    content = content.trim();
                    if (content) {
                        const sentences = content.split('.');
                        summary = sentences[0].substring(0, 150);
                        if (sentences[0].length > 150 || sentences.length > 1) {
                            summary += '...';
                        }
                    }
                }
                
                // If no summary from preview, try description
                if (!summary && item.description) {
                    summary = item.description.substring(0, 150);
                    if (item.description.length > 150) {
                        summary += '...';
                    }
                }
                
                // Add additional metadata based on type
                const result = {
                    id: id,
                    title: title,
                    url: url,
                    type: itemType,
                    summary: summary || 'No summary available'
                };

                // Add type-specific metadata
                if (item.book_id) result.book_id = item.book_id;
                if (item.chapter_id) result.chapter_id = item.chapter_id;
                if (item.slug) result.slug = item.slug;
                if (item.created_at) result.created_at = item.created_at;
                if (item.updated_at) result.updated_at = item.updated_at;
                
                // Add tags if present
                if (item.tags && Array.isArray(item.tags) && item.tags.length > 0) {
                    result.tags = item.tags;
                }

                simplifiedResults.push(result);
            }
        }
        
        // Return simplified format with metadata
        const searchResponse = {
            query: args.query,
            total: data.total || 0,
            page: args.page || 1,
            count: args.count || simplifiedResults.length,
            results: simplifiedResults
        };
        
        return {
            content: [{
                type: 'text',
                text: JSON.stringify(searchResponse, null, 2),
            }],
        };

    } catch (error) {
        console.error('Error in handleSearchBookstack:', error);
        return {
            content: [{
                type: 'text',
                text: JSON.stringify({ 
                    error: `Search failed: ${error.message}`,
                    details: error.stack
                }, null, 2),
            }],
            isError: true
        };
    }
}

/**
 * Tool definition for searching BookStack content
 */
export const searchBookstackToolDefinition = {
    name: 'search_bookstack',
    description: 'Search content across all BookStack content types (shelves, books, chapters, pages). Supports advanced search syntax.',
    inputSchema: {
        type: 'object',
        properties: {
            query: {
                type: 'string',
                description: 'The search query string. Supports advanced BookStack search syntax (e.g., "cats {created_by:me}", "tag:important").'
            },
            page: {
                type: 'number',
                description: 'Page number for pagination (minimum: 1)',
                minimum: 1
            },
            count: {
                type: 'number',
                description: 'Number of results per page (minimum: 1, maximum: 100)',
                minimum: 1,
                maximum: 100
            }
        },
        required: ['query']
    }
};
