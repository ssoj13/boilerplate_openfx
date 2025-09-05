#pragma once

#include "ofxsImageEffect.h"
#include "ofxsMultiThread.h"

#include <memory>

class ColorFillPlugin : public OFX::ImageEffect {
public:
    ColorFillPlugin(OfxImageEffectHandle handle);
    virtual void render(const OFX::RenderArguments &args) override final;

private:
    // Do not need to delete these, the ImageEffect is managing them for us
    OFX::Clip *_dstClip;
    OFX::RGBAParam *_color;
};

class ColorFillPluginFactory : public OFX::PluginFactoryHelper<ColorFillPluginFactory> {
public:
    ColorFillPluginFactory();
    virtual void describe(OFX::ImageEffectDescriptor &desc) override final;
    virtual void describeInContext(OFX::ImageEffectDescriptor &desc, OFX::ContextEnum context) override final;
    virtual OFX::ImageEffect* createInstance(OfxImageEffectHandle handle, OFX::ContextEnum context) override final;
};
