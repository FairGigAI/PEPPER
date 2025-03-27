import React from 'react';
import './UserProfile.css';

interface UserProfileProps {
    name: any;
    email: any;
    avatar: any;
}

export const UserProfile: React.FC<UserProfileProps> = (name, email, avatar) => {
    return (
        <div className="userprofile-container">
            <h1>UserProfile</h1>
            {/* Add component content here */}
        </div>
    );
};
