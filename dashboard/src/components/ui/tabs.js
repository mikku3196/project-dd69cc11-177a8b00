
import React, { createContext, useContext, useState } from 'react';
import { cn } from '../../utils/cn';

const TabsContext = createContext();

export const Tabs = ({ defaultValue, value, onValueChange, className, children, ...props }) => {
  const [internalValue, setInternalValue] = useState(defaultValue);
  const currentValue = value !== undefined ? value : internalValue;
  
  const handleValueChange = (newValue) => {
    if (value === undefined) {
      setInternalValue(newValue);
    }
    onValueChange?.(newValue);
  };
  
  return (
    <TabsContext.Provider value={{ value: currentValue, onValueChange: handleValueChange }}>
      <div className={cn("w-full", className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  );
};

export const TabsList = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground",
      className
    )}
    {...props}
  />
));
TabsList.displayName = "TabsList";

export const TabsTrigger = React.forwardRef(({ className, value, ...props }, ref) => {
  const context = useContext(TabsContext);
  const isActive = context.value === value;
  
  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        isActive && "bg-background text-foreground shadow-sm",
        className
      )}
      onClick={() => context.onValueChange(value)}
      {...props}
    />
  );
});
TabsTrigger.displayName = "TabsTrigger";

export const TabsContent = React.forwardRef(({ className, value, ...props }, ref) => {
  const context = useContext(TabsContext);
  
  if (context.value !== value) {
    return null;
  }
  
  return (
    <div
      ref={ref}
      className={cn(
        "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className
      )}
      {...props}
    />
  );
});
TabsContent.displayName = "TabsContent";
