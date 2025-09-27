/**
 * Tool handler for updating a chapter in Bookstack
 */
export async function handleUpdateChapter(server, args) {
    try {
        // Validate arguments
        if (!args.id || typeof args.id !== 'number' || args.id <= 0) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Valid chapter ID is required" }, null, 2),
                }],
                isError: true
            };
        }
        
        if (!args.book_id && !args.name && !args.description && !args.tags && !args.priority) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "At least one field to update must be provided" }, null, 2),
                }],
                isError: true
            };
        }

        // Get environment variables
        // Use the provided credentials directly
        const baseUrl = "https://knowledge.oculair.ca";
        const tokenId = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT";
        const tokenSecret = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE";

        console.log(`Using Bookstack API at ${baseUrl} to update chapter with ID ${args.id}`);

        // Set up request headers
        const headers = {
            'Authorization': `Token ${tokenId}:${tokenSecret}`,
            'Content-Type': 'application/json'
        };

        try {
            // Get current chapter data first
            const controller1 = new AbortController();
            const timeoutId1 = setTimeout(() => controller1.abort(), 30000); // 30 seconds timeout
            
            const currentChapterResponse = await fetch(`${baseUrl.replace(/\/$/, '')}/api/chapters/${args.id}`, {
                method: 'GET',
                headers: headers,
                signal: controller1.signal
            });
            
            clearTimeout(timeoutId1);
            
            if (!currentChapterResponse.ok) {
                throw new Error(`Failed to retrieve current chapter data - HTTP error! Status: ${currentChapterResponse.status}`);
            }
            
            const currentData = await currentChapterResponse.json();
            
            // Prepare update payload with current values as defaults
            const payload = {
                book_id: args.book_id !== undefined ? args.book_id : currentData.book_id,
                name: args.name !== undefined ? args.name : currentData.name || "",
                description: args.description !== undefined ? args.description : currentData.description || ""
            };
            
            if (args.tags !== undefined) {
                payload.tags = args.tags;
            }
            
            if (args.priority !== undefined) {
                payload.priority = args.priority;
            }
            
            // Make the update API request
            const controller2 = new AbortController();
            const timeoutId2 = setTimeout(() => controller2.abort(), 30000); // 30 seconds timeout
            
            const response = await fetch(`${baseUrl.replace(/\/$/, '')}/api/chapters/${args.id}`, {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify(payload),
                signal: controller2.signal
            });
            
            clearTimeout(timeoutId2);
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify(data, null, 2),
                }],
            };
        } catch (error) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ 
                        error: `Network or HTTP error - ${error.message}` 
                    }, null, 2),
                }],
                isError: true
            };
        }
    } catch (error) {
        return server.createErrorResponse(error);
    }
}

/**
 * Tool definition for update_chapter
 */
export const updateChapterToolDefinition = {
    name: 'update_chapter',
    description: 'Updates a chapter in Bookstack',
    inputSchema: {
        type: 'object',
        properties: {
            id: {
                type: 'number',
                description: 'The ID of the chapter to update',
            },
            book_id: {
                type: 'number',
                description: 'The ID of the book to move the chapter to',
            },
            name: {
                type: 'string',
                description: 'The new name of the chapter',
            },
            description: {
                type: 'string',
                description: 'A new description of the chapter',
            },
            tags: {
                type: 'array',
                items: {
                    type: 'object',
                    properties: {
                        name: { type: 'string' },
                        value: { type: 'string' }
                    },
                    required: ['name', 'value'],
                    additionalProperties: false
                },
                description: 'A new list of tag objects (each with "name" and "value")',
            },
            priority: {
                type: 'number',
                description: 'New chapter priority',
            },
        },
        required: ['id'],
    },
};