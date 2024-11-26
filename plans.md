# Conversation Summary Framework

## Overview
I explored the development of a backend system for a dungeon crawler game using Unreal Engine 4.27.2, focusing on integrating a PDF processing server for generating study questions. The primary objectives included determining the best approach for database integration within Unreal and outlining the server's role in processing PDF files.

## Key Points and Developments

1. **Initial Goals/Questions**
   - **Objective**: To create a backend system that allows users to upload textbooks and generate questions for study purposes.
     - **Notes**: The majority of the backend system is implemeneted
   - **Constraints**: The system must efficiently handle PDF parsing and question generation while integrating seamlessly with the Unreal Engine environment.
     - **Notes**: PDF have a lot of text, searching through them does take a bit of time because there are many words

2. **Major Insights and Decisions**
   - **Server Processing**: All PDF parsing and question generation will occur on a cloud server (AWS EC2) and has already been tested locally, allowing for efficient resource management and offloading heavy processing from the game client.

3. **Solutions/Ideas Generated**
   - **Option 1: Develop Database Logic Separately**
     - **Description**: Set up a minimal Unreal project with SimpleSQLite plugin to develop and test database logic
     - **Benefits**: 
       * Focused development environment
       * Easier to test database operations
       * Can create a clean implementation guide for the team
     - **Challenges**: 
       * Need to reinstall SimpleSQLite plugin when integrating with main project
       * May miss some game-specific context
     - **Implementation Considerations**: 
       * Document all database setup steps
       * Create blueprint function library for common operations
       * Test thoroughly before integration

   - **Option 2: Clone and Integrate Directly**
     - **Description**: Clone the game project, install SimpleSQLite plugin, and develop database functionality there
     - **Benefits**: 
       * Immediate access to game context and requirements
       * Can test with actual game scenarios
       * One-time plugin installation
       * Easier to adapt to ongoing game changes
     - **Challenges**: 
       * Need to coordinate with team's ongoing development
       * More complex testing environment
     - **Implementation Considerations**: 
       * Create a separate branch for database implementation
       * Regular syncs with main development branch

4. **Action Items and Next Steps**
   - **Action Item 1**: Develop the SQLite database module as a separate plugin (High priority).
   - **Action Item 2**: Create documentation and integration guidelines for team members (Medium priority).
   - **Action Item 3**: Set up the cloud server (AWS EC2) for PDF processing (High priority).
   - **Action Item 4**: Discuss with the team about the final decision on question generation during gameplay (Medium priority).

## Technical Details
- **Methodologies**: Use FastAPI for the server-side application, SQLite for local database management, and HTTP requests for communication between the game and server.
- **Technical Requirements**: Python environment for the server, SQLite library for Unreal, and HTTP plugin for Unreal Engine.
- **Resource Considerations**: Server resources for handling PDF processing and storage for generated questions.

## Open Questions
- What is the optimal number of questions to generate per chapter?
- How will the game handle user interactions for uploading and selecting textbooks?
- What are the best practices for managing database migrations as the project evolves?

## Additional Notes
- The game will prompt users to select or upload textbooks, with a confirmation step before processing.
- The server will handle PDF parsing and question generation, returning data to be stored locally in the game.
- The discussion emphasized the importance of modular development to facilitate integration with ongoing game logic.

## Summary Metrics
- **Duration of conversation**: Approximately 1 hour
- **Number of main topics covered**: 3
- **Number of action items generated**: 4
- **Number of solutions proposed**: 2

## Next Steps
1. **Immediate Next Actions**: Start developing the SQLite database module with Unreal Engine.
2. **Suggested Follow-Up Topics**: Discuss the integration of the database module with the game logic and finalize the question generation strategy.
3. **Recommendations for Future Discussions**: Regular check-ins on the progress of the database integration and server setup, as well as discussions on user experience for textbook selection and question generation.

### Key Takeaways
- The backend system will utilize a cloud server for PDF processing, ensuring efficient resource management.
- A separate SQLite database module will be developed for easy integration with Unreal Engine.
- Clear documentation and guidelines will be essential for team collaboration and integration efforts.